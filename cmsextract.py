import aiohttp
import asyncio
import time

def banner():
    print("\033[96m" + """
   ██████  ███▄ ▄███▓ ███▄    █   █████▒██▓ ███▄    █  ▄▄▄       ▄████▄  
 ▒██    ▒ ▓██▒▀█▀ ██▒ ██ ▀█   █ ▓██   ▒▓██▒ ██ ▀█   █ ▒████▄    ▒██▀ ▀█  
 ░ ▓██▄   ▓██    ▓██░▓██  ▀█ ██▒▒████ ░▒██▒▓██  ▀█ ██▒▒██  ▀█▄  ▒▓█    ▄ 
   ▒   ██▒▒██    ▒██ ▓██▒  ▐▌██▒░▓█▒  ░░██░▓██▒  ▐▌██▒░██▄▄▄▄██ ▒▓▓▄ ▄██▒
 ▒██████▒▒▒██▒   ░██▒▒██░   ▓██░░▒█░   ░██░▒██░   ▓██░ ▓█   ▓██▒▒ ▓███▀ ░
 ▒ ▒▓▒ ▒ ░░ ▒░   ░  ░░ ▒░   ▒ ▒  ▒ ░   ░▓  ░ ▒░   ▒ ▒  ▒▒   ▓▒█░░ ░▒ ▒  ░
 ░ ░▒  ░ ░░  ░      ░░ ░░   ░ ▒░ ░      ▒ ░░ ░░   ░ ▒░  ▒   ▒▒ ░  ░  ▒   
 ░  ░  ░  ░      ░    ░   ░ ░  ░ ░    ░ ▒ ░   ░   ░ ░   ░   ▒   ░        
       ░         ░          ░           ░           ░       ░  ░░ ░      
                                                             ░          
               A Tool for Extracting CMS Information
""" + "\033[0m")


# Retry decorator for retrying failed requests
async def retry_request(session, site, max_retries=3):
    retries = 0
    while retries < max_retries:
        try:
            async with session.get(site, timeout=20) as response:  # Increase timeout to 20 seconds
                return await response.text()
        except asyncio.TimeoutError:
            print(f"\033[91m[-] Timeout Error: Retrying {site} ({retries + 1}/{max_retries})\033[0m")
        except Exception as e:
            print(f"\033[91m[-] Error with {site}: {e}\033[0m")
        retries += 1
        await asyncio.sleep(2)  # Wait for 2 seconds before retrying
    return None  # Return None if max retries exceeded

# CMS Detection function
async def cms_detected(session, site, semaphore):
    site = site.rstrip()
    print(f"\033[91m[+] \033[95mScanning... \033[94m{site} \033[91m[+]")

    async with semaphore:  # Limit concurrent requests
        response_text = await retry_request(session, site)

        if response_text is None:
            print(f"\033[91m[-] Failed to retrieve {site} after retries.\033[0m")
            return

        try:
            # Check for CMS markers in response
            if "wp-content" in response_text:
                print(f"\033[92mWordPress Site: >>>>>>>>>>>>>>\033[91m {site}/wp-login.php")
                with open("wp_sites.txt", "a") as wpp:
                    wpp.write(f"{site}/wp-login.php\n")

            elif "com_content" in response_text:
                print(f"\033[92mJoomla Site: >>>>>>>>>>>>>>\033[91m {site}/administrator/")
                with open("joomla_sites.txt", "a") as jmm:
                    jmm.write(f"{site}/administrator/\n")

            elif "index.php?route" in response_text:
                print(f"\033[92mOpenCart Site: >>>>>>>>>>>>>>\033[91m {site}/admin/")
                with open("opencart_sites.txt", "a") as opncrt:
                    opncrt.write(f"{site}/admin/\n")

            elif "/node/" in response_text:
                print(f"\033[92mDrupal Site: >>>>>>>>>>>>>>\033[91m {site}/user/login")
                with open("drupal_sites.txt", "a") as drbl:
                    drbl.write(f"{site}/user/login\n")

            else:
                bypass = ["/admin/login.php", "/admin/", "/login.php", "/admin.html", "/admin.php", "/member/"]
                for byp in bypass:
                    bypass_response_text = await retry_request(session, site + byp)
                    if bypass_response_text and 'type="password"' in bypass_response_text:
                        print(f"\033[92mAdmin Panel Found: >>>>>>>>>>>>>>\033[91m {site + byp}")
                        with open("admin_sites.txt", "a") as by:
                            by.write(f"{site + byp}\n")
                        break
                else:
                    print(f"\033[91m[-] No CMS Detected: [-] \033[91m{site}")

        except Exception as e:
            print(f"\033[91m[-] Error during CMS detection for {site}: {e}\033[0m")


async def main():
    banner()
    list_sites = input("Enter the file name with the list of sites: ")
    with open(list_sites, 'r') as lst:
        sites = lst.readlines()

    # Semaphore to limit the number of concurrent connections
    semaphore = asyncio.Semaphore(20)  # Adjust the number of allowed concurrent tasks

    async with aiohttp.ClientSession() as session:
        tasks = []
        for site in sites:
            task = asyncio.ensure_future(cms_detected(session, site, semaphore))
            tasks.append(task)

        await asyncio.gather(*tasks)


if __name__ == "__main__":
    start_time = time.time()
    asyncio.run(main())
    end_time = time.time()
    print(f"\033[92mFinished Scanning in {end_time - start_time:.2f} seconds.\033[0m")
