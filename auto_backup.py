import os
import shutil
import datetime
import time
import stat

def backup_database():
    source_file = "/home/ubuntu/Jincai_Radio_System/instance/database.db"
    backup_folder = "/home/ubuntu/Jincai_Radio_System/backup"
    max_files = 100

    # 获取当前日期和时间
    now = datetime.datetime.now()
    date_string = now.strftime("%Y-%m-%d")
    time_string = now.strftime("%H:%M:%S")

    # 构建备份文件名
    backup_file = f"{date_string}_database_{time_string}.db"

    # 创建备份文件夹（如果不存在）
    if not os.path.exists(backup_folder):
        os.makedirs(backup_folder)

    # 复制数据库文件到备份文件夹
    shutil.copy(source_file, os.path.join(backup_folder, backup_file))

    # 设置备份文件为只读属性
    backup_file_path = os.path.join(backup_folder, backup_file)
    os.chmod(backup_file_path, stat.S_IREAD)

    print("文件复制成功：", backup_file)

    # 删除最早的文件，如果文件数量超过限制
    file_list = os.listdir(backup_folder)
    if len(file_list) > max_files:
        oldest_file = min(file_list)
        os.remove(os.path.join(backup_folder, oldest_file))
        print("文件删除成功：", oldest_file)

    # 打印本次备份的日期时间和下次备份的日期时间
    next_backup = now + datetime.timedelta(days=1)
    next_backup_date = next_backup.date()
    next_backup_time = next_backup.time()
    print("本次备份时间：", now)
    print("下次备份时间：", next_backup_date, next_backup_time)

# 执行一次初始备份
backup_database()

# 获取当前日期
today = datetime.datetime.now().date()

# 计算下一个执行备份任务的日期
next_backup = today + datetime.timedelta(days=1)

# 计算下一个执行备份任务的时间
next_backup_time = datetime.datetime.combine(next_backup, datetime.time(hour=0, minute=0, second=0))

# 计算当前时间与下一个备份时间之间的时间差
time_delta = next_backup_time - datetime.datetime.now()

# 等待时间差所指定的时间
time.sleep(time_delta.total_seconds())

# 每天执行一次备份任务
while True:
    backup_database()

    # 计算下一个执行备份任务的日期
    next_backup = next_backup + datetime.timedelta(days=1)

    # 计算下一个执行备份任务的时间
    next_backup_time = datetime.datetime.combine(next_backup, datetime.time(hour=0, minute=0, second=0))

    # 计算当前时间与下一个备份时间之间的时间差
    time_delta = next_backup_time - datetime.datetime.now()

    # 等待时间差所指定的时间
    time.sleep(time_delta.total_seconds())
