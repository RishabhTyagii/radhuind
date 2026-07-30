import pandas as pd
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Sum
from django.utils import timezone
from .models import Party, Order, OrderItem
from stock.models import TyreItem
from cycletube.models import CycleTubeItem
from cycletyres.models import CycleTyreItem


def has_orders_access(user):
    if user.is_superuser:
        return True
    profile = getattr(user, 'profile', None)
    allowed = getattr(profile, 'allowed_pages', []) if profile else []
    return 'my_orders' in allowed


def has_admin_orders_access(user):
    if user.is_superuser:
        return True
    profile = getattr(user, 'profile', None)
    allowed = getattr(profile, 'allowed_pages', []) if profile else []
    return 'admin_orders' in allowed


def _build_stock_data(user):
    """Build stock availability across all 3 categories."""
    stock_data = []

    # --- Auto Tyre ---
    for item in TyreItem.objects.filter(is_active=True):
        my_qty = OrderItem.objects.filter(
            category='auto_tyre', tyre_item=item,
            order__user=user, order__status='pending'
        ).aggregate(s=Sum('quantity'))['s'] or 0

        other_qty = OrderItem.objects.filter(
            category='auto_tyre', tyre_item=item, order__status='pending'
        ).exclude(order__user=user).aggregate(s=Sum('quantity'))['s'] or 0

        stock_data.append({
            'category': 'auto_tyre',
            'category_label': 'Auto Tyre',
            'id': f'auto_{item.id}',
            'display': f"{item.tyre} {item.pattern} {item.type}",
            'total_stock': item.stock,
            'my_orders': my_qty,
            'other_orders': other_qty,
            'available': item.stock - my_qty - other_qty,
        })

    # --- Cycle Tube ---
    for item in CycleTubeItem.objects.filter(is_active=True):
        my_qty = OrderItem.objects.filter(
            category='cycle_tube', tube_item=item,
            order__user=user, order__status='pending'
        ).aggregate(s=Sum('quantity'))['s'] or 0

        other_qty = OrderItem.objects.filter(
            category='cycle_tube', tube_item=item, order__status='pending'
        ).exclude(order__user=user).aggregate(s=Sum('quantity'))['s'] or 0

        stock_data.append({
            'category': 'cycle_tube',
            'category_label': 'Cycle Tube',
            'id': f'tube_{item.id}',
            'display': f"{item.size} {item.type} {item.brand}",
            'total_stock': item.stock,
            'my_orders': my_qty,
            'other_orders': other_qty,
            'available': item.stock - my_qty - other_qty,
        })

    # --- Cycle Tyre ---
    for item in CycleTyreItem.objects.filter(is_active=True):
        my_qty = OrderItem.objects.filter(
            category='cycle_tyre', cycle_tyre_item=item,
            order__user=user, order__status='pending'
        ).aggregate(s=Sum('quantity'))['s'] or 0

        other_qty = OrderItem.objects.filter(
            category='cycle_tyre', cycle_tyre_item=item, order__status='pending'
        ).exclude(order__user=user).aggregate(s=Sum('quantity'))['s'] or 0

        stock_data.append({
            'category': 'cycle_tyre',
            'category_label': 'Cycle Tyre',
            'id': f'ctyre_{item.id}',
            'display': f"{item.size} {item.box_type} {item.brand}",
            'total_stock': item.stock,
            'my_orders': my_qty,
            'other_orders': other_qty,
            'available': item.stock - my_qty - other_qty,
        })

    return stock_data


@login_required
@user_passes_test(has_orders_access)
def my_orders(request):
    parties = Party.objects.filter(user=request.user)
    orders = Order.objects.filter(user=request.user).prefetch_related('items', 'party')

    if request.method == 'POST':
        if 'add_party' in request.POST:
            party_name = request.POST.get('party_name', '').strip()
            if party_name:
                Party.objects.get_or_create(user=request.user, name=party_name)
                messages.success(request, f'Party "{party_name}" added!')
        return redirect('my_orders')

    return render(request, 'orders/my_orders.html', {'parties': parties, 'orders': orders})


@login_required
@user_passes_test(has_orders_access)
def create_order(request):
    parties = Party.objects.filter(user=request.user)
    stock_data = _build_stock_data(request.user)

    if request.method == 'POST':
        party_id = request.POST.get('party_id')
        deadline = request.POST.get('deadline') or None
        notes = request.POST.get('notes', '').strip()

        if not party_id:
            messages.error(request, 'Please select a party.')
            return render(request, 'orders/create_order.html', {'parties': parties, 'stock_data': stock_data})

        party = get_object_or_404(Party, id=party_id, user=request.user)
        order = Order.objects.create(user=request.user, party=party, deadline=deadline, notes=notes or None)

        items_added = 0
        for key, value in request.POST.items():
            if not value or value == '0':
                continue
            try:
                qty = int(value)
                if qty <= 0:
                    continue
            except ValueError:
                continue

            if key.startswith('auto_'):
                item_id = int(key.replace('auto_', ''))
                tyre = TyreItem.objects.get(id=item_id)
                OrderItem.objects.create(order=order, category='auto_tyre', tyre_item=tyre, quantity=qty)
                items_added += 1
            elif key.startswith('tube_'):
                item_id = int(key.replace('tube_', ''))
                tube = CycleTubeItem.objects.get(id=item_id)
                OrderItem.objects.create(order=order, category='cycle_tube', tube_item=tube, quantity=qty)
                items_added += 1
            elif key.startswith('ctyre_'):
                item_id = int(key.replace('ctyre_', ''))
                ctyre = CycleTyreItem.objects.get(id=item_id)
                OrderItem.objects.create(order=order, category='cycle_tyre', cycle_tyre_item=ctyre, quantity=qty)
                items_added += 1

        if items_added == 0:
            order.delete()
            messages.error(request, 'No items were added. Please enter at least one quantity.')
            return render(request, 'orders/create_order.html', {'parties': parties, 'stock_data': stock_data})

        messages.success(request, f'Order #{order.id} placed successfully with {items_added} item(s)!')
        return redirect('order_detail', order_id=order.id)

    return render(request, 'orders/create_order.html', {'parties': parties, 'stock_data': stock_data})


@login_required
def order_detail(request, order_id):
    # Employee can only view own orders; admin can view all
    if request.user.is_superuser or (hasattr(request.user, 'profile') and 'admin_orders' in (request.user.profile.allowed_pages or [])):
        order = get_object_or_404(Order, id=order_id)
    else:
        order = get_object_or_404(Order, id=order_id, user=request.user)

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'update_status':
            new_status = request.POST.get('status')
            if new_status in dict(Order.STATUS_CHOICES):
                order.status = new_status
                if new_status in ('completed', 'cancelled'):
                    order.resolved_by = request.user
                    order.resolved_at = timezone.now()
                order.save()
                messages.success(request, f'Order status updated to "{order.get_status_display()}".')
        return redirect('order_detail', order_id=order.id)

    return render(request, 'orders/order_detail.html', {
        'order': order,
        'status_choices': Order.STATUS_CHOICES,
    })


@login_required
@user_passes_test(has_admin_orders_access)
def admin_orders(request):
    orders = Order.objects.all().select_related('user', 'party', 'resolved_by').prefetch_related('items')
    return render(request, 'orders/admin_orders.html', {'orders': orders})


@login_required
@user_passes_test(has_orders_access)
def import_orders(request):
    if request.method == 'POST' and request.FILES.get('excel_file'):
        excel_file = request.FILES['excel_file']
        party_id = request.POST.get('party_id')
        party = get_object_or_404(Party, id=party_id, user=request.user)

        try:
            df = pd.read_excel(excel_file)
            order = Order.objects.create(user=request.user, party=party)
            items_added = 0

            for index, row in df.iterrows():
                try:
                    tyre = str(row.get('Tyre', '')).strip()
                    pattern = str(row.get('Pattern', '')).strip()
                    tt_type = str(row.get('Type', '')).strip()
                    qty = int(row.get('Quantity', 0))

                    if qty > 0 and tyre:
                        tyre_item = TyreItem.objects.filter(
                            tyre__iexact=tyre, pattern__iexact=pattern, type__iexact=tt_type
                        ).first()
                        if tyre_item:
                            OrderItem.objects.create(order=order, category='auto_tyre', tyre_item=tyre_item, quantity=qty)
                            items_added += 1
                except Exception as e:
                    print(f"Error row {index}: {e}")

            if items_added > 0:
                messages.success(request, f'Order imported with {items_added} items.')
            else:
                order.delete()
                messages.warning(request, 'No valid items found in the Excel file.')
        except Exception as e:
            messages.error(request, f'Error processing file: {str(e)}')

        return redirect('my_orders')

    parties = Party.objects.filter(user=request.user)
    return render(request, 'orders/import_orders.html', {'parties': parties})
