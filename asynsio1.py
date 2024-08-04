import time

# def normal_function():
#     print("Start normal function")
#     time.sleep(2)  # Simulate a blocking I/O operation
#     print("End normal function")

# def main():
#     start_time = time.time()
#     normal_function()
#     normal_function()
#     print(f"Total time: {time.time() - start_time} seconds")

# if __name__ == "__main__":
#     main()



import asyncio
import time
async def function1():
    print("Start asyncio coroutine")
    await asyncio.sleep(2)  # Simulate a non-blocking I/O operation
    time.sleep(2)
    print("End asyncio coroutine")

async def function2():
    print("Start2 asyncio coroutine")
    await asyncio.sleep(2)  # Simulate a non-blocking I/O operation
    # time.sleep(2)
    print("End2 asyncio coroutine")

# start_time = time.time()
# asyncio.run(function1())
# asyncio.run(function2())
# print(f"Total time: {time.time() - start_time} seconds")

async def main():
    start_time = time.time()
    await asyncio.gather(function1(), function2())
    print(f"Total time: {time.time() - start_time} seconds")

if __name__ == "__main__":
    asyncio.run(main())


#3.12.3