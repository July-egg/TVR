from datetime import datetime

dt = datetime.now()
print(dt)
a = dt.strftime('%Y/%m/%d %H:%M:%S')
print(a)