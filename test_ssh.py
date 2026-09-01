from ssh_executor import SSHExecutor


executor = SSHExecutor(
    host="127.0.0.1",
    port=2222,
    username="root",
    password="password"
)

executor.connect()

print(executor.execute("whoami"))
print(executor.execute("pwd"))
print(executor.execute("ls"))

executor.close()