from .models import LeaveBalance


def deduct_leave(attendance):

    if attendance.status != "Absent":
        return

    try:

        balance = LeaveBalance.objects.get(

            employee=attendance.employee,

            year=attendance.date.year,

        )

    except LeaveBalance.DoesNotExist:

        return

    if attendance.leave_type == "CL":

        if balance.cl_balance > 0:

            balance.cl_balance -= 1

        else:

            attendance.leave_type = "LOP"

    elif attendance.leave_type == "EL":

        if balance.el_balance > 0:

            balance.el_balance -= 1

        else:

            attendance.leave_type = "LOP"

    balance.save()