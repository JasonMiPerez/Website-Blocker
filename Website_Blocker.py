from tkinter import *
from tkinter import messagebox
from tkinter import scrolledtext
from tkinter import ttk
import tkinter as tk
import sqlite3
import os
import sys
import ctypes
import platform
import subprocess
import re
import shlex 
import shutil

# Admin Privileges ----------------------------------------------------------------------------------------------------------------------------

# Checks to see if program is being run as admin
def is_admin():
    if os.name == 'nt':
        try:
            return bool(ctypes.windll.shell32.IsUserAnAdmin())
        except Exception:
            return False
    else:
        return hasattr(os, "geteuid") and os.geteuid() == 0 

# If program is not run as admin, attempts to ask user to run program as admin, otherwise ends program
def elevate_or_exit():
    if is_admin():
        return

    system = platform.system()
    argv = " ".join(shlex.quote(a) for a in sys.argv)

    if system == "Windows":
        try:
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, " ".join(sys.argv[1:]), None, 1
            )
        except Exception as e:
            print(f"Failed to elevate privileges: {e}")
        sys.exit(0)

    elif system == "Darwin":
        try:
            script = f'do shell script {shlex.quote(sys.executable + " " + argv)} with administrator privileges'
            ret = subprocess.call(["osascript", "-e", script])
            if ret != 0:
                raise RuntimeError("osascript returned non-zero")
        except Exception as e:
            print("Elevation failed. Try running with sudo:")
            print(f"   sudo {argv}")
        sys.exit(0)

    elif system == "Linux":
        try:
            # Prefer pkexec if available
            if shutil.which("pkexec"):
                ret = subprocess.call(["pkexec", sys.executable] + sys.argv)
                if ret != 0:
                    raise RuntimeError("pkexec returned non-zero")
            else:
                raise FileNotFoundError("pkexec not found")
        except Exception as e:
            print("Elevation failed or pkexec unavailable. Try:")
            print(f"   sudo {argv}")
        sys.exit(0)

    else:
        print("Unsupported OS.")
        sys.exit(1)

# When the program runs, make sure privileges are elevated before doing anything else
if __name__ == "__main__":
    elevate_or_exit()

#----------------------------------------------------------------------------------------------------------------------------------------------------------

# Store loopback address
Loopback_Address = "127.0.0.1"

# Store host file path
if platform.system() == "Windows":
    Host_File_Path = r"C:\Windows\System32\drivers\etc\hosts"
elif platform.system() == "Darwin":
    Host_File_Path = r"/private/etc/hosts"
else:
    Host_File_Path = r"/etc/hosts"

# Checks if string is domain name
def is_domain(domain_name):
    return bool(re.search(r"^(?:www\.)?[a-zA-Z_]+\.(?:com|org|net|int|edu|gov|mil|arpa)$", domain_name))

# Check if string contains subdomain (www.)
def contains_subdomain(domain_name):
    if domain_name[:4] == "www.":
        return True
    else: 
        return False

# Blocks website
def block_website(domain_name):
    if not is_domain(domain_name):
        return
    
    try:
        if contains_subdomain(domain_name):
            with open(Host_File_Path, "a") as Host_File:
                Host_File.write(f"{Loopback_Address} {domain_name[4:]}\n")
                Host_File.write(f"{Loopback_Address} {domain_name}\n")
        else:
            with open(Host_File_Path, "a") as Host_File:
                Host_File.write(f"{Loopback_Address} {domain_name}\n")
                Host_File.write(f"{Loopback_Address} www.{domain_name}\n")
    except Exception as e:
        print(f"Error while unblocking: {e}")

# Unblocks website
def unblock_website(domain_name):
    if not is_domain(domain_name):
        return

    if contains_subdomain(domain_name):
        domains_to_remove = [f"{Loopback_Address} {domain_name[4:]}", f"{Loopback_Address} {domain_name}"]
    else:
        domains_to_remove = [f"{Loopback_Address} www.{domain_name}", f"{Loopback_Address} {domain_name}"]
    
    Lines = []
    try:
        with open(Host_File_Path, "r") as Host_File:
            for line in Host_File:
                if line.strip() not in domains_to_remove:
                    Lines.append(line)
        with open(Host_File_Path, "w") as Host_File:
            for line in Lines:
                Host_File.write(line)

    except Exception as e:
        print(f"Error while unblocking: {e}")

# Create the blocked websites database only if it does not exist
conn = sqlite3.connect('websites_blocked.db')

cursor = conn.cursor()

cursor.execute("""CREATE TABLE IF NOT EXISTS websites_blocked(
               names string,
               domains string 
               )""")

conn.commit()

conn.close()

# Structure of the Website Blocker Program ----------------------------------------------------------------------------------------------------

# Create root widget
root = Tk()
root.title("Website Blocker")
root.geometry("400x450")

# Create entry for user to block websites
Block_Website_Entry_Title = Label(root, text="Enter Websites to Block")
Block_Website_Entry_Title.grid(row = 0, column = 0, padx = (0,0), pady = (20,0), columnspan = 2)
Block_Website_Name_Entry = Entry(root, width = 50)
Block_Website_Name_Entry.grid(row = 1, column = 1, sticky = "w")
Block_Website_Domain_Entry = Entry(root, width = 50)
Block_Website_Domain_Entry.grid(row = 2, column = 1, sticky = "w")
Block_Website_Name_Entry_Title = Label(root, text="Name", anchor = "e")
Block_Website_Name_Entry_Title.grid(row = 1, column = 0, sticky = "e")
Block_Website_Domain_Entry_Title = Label(root, text="Domain", anchor = "e")
Block_Website_Domain_Entry_Title.grid(row = 2, column = 0, sticky = "e") 
Block_Website_Button = Button(root, text="Enter", command=lambda: block_website_GUI(Block_Website_Name_Entry.get(),Block_Website_Domain_Entry.get()))
Block_Website_Button.grid(row = 3, column = 0, columnspan = 2, padx = (0,0), pady = (10,0))

# Create entry for user to unblock websites
Unblock_Website_Entry_Title = Label(root, text="Enter Websites to Unblock")
Unblock_Website_Entry_Title.grid(row = 4, column = 0, padx = (0,0), pady = (20,0), columnspan = 2)
Unblock_Website_Domain_Entry = Entry(root, width = 50)
Unblock_Website_Domain_Entry.grid(row = 5, column = 1, sticky = "w")
Unblock_Website_Domain_Entry_Title = Label(root, text="Domain", anchor = "e")
Unblock_Website_Domain_Entry_Title.grid(row = 5, column = 0, sticky = "e")
Unblock_Website_Domain_Button = Button(root, text="Enter", command=lambda: unblock_website_GUI(Unblock_Website_Domain_Entry.get()))
Unblock_Website_Domain_Button.grid(row = 6, column = 0, columnspan = 2, padx = (0,0), pady = (10,0))

# Create entry for user to search for blocked websites in database
Search_Database_for_Website_Entry_Title = Label(root, text="Search for Websites that are Blocked")
Search_Database_for_Website_Entry_Title.grid(row = 7, column = 0, padx = (0,0), pady = (20,0), columnspan = 2)
Search_Database_for_Website_Name_Entry = Entry(root, width = 50)
Search_Database_for_Website_Name_Entry.grid(row = 8, column = 1, sticky = "w")
Search_Database_for_Website_Name_Entry_Title = Label(root, text="Name", anchor = "e")
Search_Database_for_Website_Name_Entry_Title.grid(row = 8, column = 0, sticky = "e")
Search_Database_for_Website_Domain_Entry = Entry(root, width = 50)
Search_Database_for_Website_Domain_Entry.grid(row = 9, column = 1, sticky = "w")
Search_Database_for_Website_Domain_Entry_Title = Label(root, text="Domain", anchor = "e")
Search_Database_for_Website_Domain_Entry_Title.grid(row = 9, column = 0, sticky = "e")
Search_Database_for_Website_Name_Button = Button(root, text="Search by Name", command = lambda: seeBlockedWebsitesByName(Search_Database_for_Website_Name_Entry.get()))
Search_Database_for_Website_Name_Button.grid(row = 10, column = 0, columnspan = 2, padx = (0,0), pady = (10,0))
Search_Database_for_Website_Domain_Button = Button(root, text="Search by Domain", command = lambda: seeBlockedWebsitesByDomain(Search_Database_for_Website_Domain_Entry.get()))
Search_Database_for_Website_Domain_Button.grid(row = 11, column = 0, columnspan = 2, padx = (0,0), pady = (10,0))

# Create button to see the entire database of blocked websites
See_Entire_Database_of_Blocked_Websites_Button = Button(root, text="See Entire Database of Blocked Websites", command=lambda: seeAllBlockedWebsites())
See_Entire_Database_of_Blocked_Websites_Button.grid(row = 12, column = 0, padx = (0,0), pady = (20,0), columnspan = 2)

root.grid_columnconfigure(0, weight = 1)
root.grid_columnconfigure(1, weight = 1)

#----------------------------------------------------------------------------------------------------------------------------------------------------------

# Clears all entries
def clearAllEntries():
    Block_Website_Name_Entry.delete(0,tk.END)
    Block_Website_Domain_Entry.delete(0,tk.END)
    Unblock_Website_Domain_Entry.delete(0,tk.END)
    Search_Database_for_Website_Name_Entry.delete(0,tk.END)
    Search_Database_for_Website_Domain_Entry.delete(0,tk.END)

# Checks to see if domain is in database
def searchByDomain(domain_name):
    if not is_domain(str(domain_name).strip()):
        return
    
    conn = sqlite3.connect('websites_blocked.db')

    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM websites_blocked WHERE domains = ?", (str(domain_name).strip(),))
    count = cursor.fetchone()[0]

    conn.commit()

    conn.close()

    if count > 0:
        return True
    else:
        return False    

# Function for blocking websites using the search bar in the GUI
def block_website_GUI(name, domain_name):
    if not is_domain(str(domain_name).strip()) or str(name).strip() == "":
        messagebox.showerror("Error","Invalid Input!\nEnter proper name and domain.\n(ex. Google and www.google.com or Google and google.com)")
        clearAllEntries()
        return
    elif searchByDomain(str(domain_name).strip()):
        messagebox.showerror("Error","Invalid Input!\nThis domain has already been blocked.")
        clearAllEntries()
        return
    
    block_website(str(domain_name).strip())

    conn = sqlite3.connect('websites_blocked.db')

    cursor = conn.cursor()

    if contains_subdomain(str(domain_name).strip()):
        cursor.execute("INSERT INTO websites_blocked (names, domains) VALUES (?,?)", (str(name).strip(),str(domain_name).strip()[4:]))
        cursor.execute("INSERT INTO websites_blocked (names, domains) VALUES (?,?)", (str(name).strip(),str(domain_name).strip()))
    else:
        cursor.execute("INSERT INTO websites_blocked (names, domains) VALUES (?,?)", (str(name).strip(),str(domain_name).strip()))
        cursor.execute("INSERT INTO websites_blocked (names, domains) VALUES (?,?)", (str(name).strip(),f"www.{str(domain_name).strip()}"))

    conn.commit()

    conn.close()

    clearAllEntries()

# Function for unblocking websites using the search bar in the GUI
def unblock_website_GUI(domain_name):
    if not searchByDomain(str(domain_name).strip()):
        messagebox.showerror("Error", "Invalid Input!\nThis domain is not blocked.")
        clearAllEntries()
        return
    
    unblock_website(str(domain_name).strip())

    conn = sqlite3.connect('websites_blocked.db')

    cursor = conn.cursor()

    if contains_subdomain(str(domain_name).strip()):
        cursor.execute("DELETE FROM websites_blocked WHERE domains = ?", (str(domain_name).strip()[4:],))
        cursor.execute("DELETE FROM websites_blocked WHERE domains = ?", (str(domain_name).strip(),))
    else:
        cursor.execute("DELETE FROM websites_blocked WHERE domains = ?", (str(domain_name).strip(),))
        cursor.execute("DELETE FROM websites_blocked WHERE domains = ?", (f"www.{str(domain_name).strip()}",))
    
    conn.commit()

    conn.close()

    clearAllEntries()

def seeBlockedWebsitesByName(name):

    top = Toplevel()
    top.title(f"Blocked Websites with Name {name}")
    top.geometry("600x600")

    frame = ttk.Frame(top)
    frame.pack(fill="both",expand=True)

    listOfBlockedWebsitesFoName = ttk.Treeview(frame)
    listOfBlockedWebsitesFoName['columns'] = ("#","Name","Domain")
    listOfBlockedWebsitesFoName.column("#0", width = 0, stretch=NO)
    listOfBlockedWebsitesFoName.column("#", width = 120, anchor = W)
    listOfBlockedWebsitesFoName.column("Name", width = 120, anchor = W)
    listOfBlockedWebsitesFoName.column("Domain", width = 120, anchor = W)
    listOfBlockedWebsitesFoName.heading("#0", text="")
    listOfBlockedWebsitesFoName.heading("#",text="Index", anchor = W)
    listOfBlockedWebsitesFoName.heading("Name",text="Name", anchor = W)
    listOfBlockedWebsitesFoName.heading("Domain",text="Domain", anchor = W)
    verticalScrollbar = ttk.Scrollbar(frame, orient="vertical", command=listOfBlockedWebsitesFoName.yview)
    verticalScrollbar.pack(side=RIGHT,fill=Y)
    listOfBlockedWebsitesFoName.pack(fill = "both", expand = True)
    listOfBlockedWebsitesFoName.configure(yscrollcommand=verticalScrollbar.set)

    conn = sqlite3.connect('websites_blocked.db')

    cursor = conn.cursor()

    cursor.execute("SELECT * FROM websites_blocked WHERE names LIKE ?", (str(name).strip(),))
    domain_entries = cursor.fetchall()
    for index, domain_entry in enumerate(domain_entries):
        name, domain = domain_entry
        listOfBlockedWebsitesFoName.insert(parent='',index='end',iid=index,text="",values=(index + 1,name,domain))

    conn.commit()

    conn.close()

    clearAllEntries()

def seeBlockedWebsitesByDomain(domain_name):
    if not is_domain(str(domain_name).strip()):
        messagebox.showerror("Error","Invalid Input!\nEnter proper name and domain.\n(ex. Google and www.google.com or Google and google.com)")
        clearAllEntries()
        return
        
    if searchByDomain(domain_name):
        if contains_subdomain(str(domain_name).strip()):
            messagebox.showinfo("Found",f"The domain {domain_name[4:]} and {domain_name} was found.")
        else:
            messagebox.showinfo("Found",f"The domain {domain_name} and www.{domain_name} was found.")
    else:
        if contains_subdomain(str(domain_name).strip()):
            messagebox.showinfo("Not Found",f"The domain {domain_name[4:]} and {domain_name} was not found.")
        else:
            messagebox.showinfo("Not Found",f"The domain {domain_name} and www.{domain_name} was not found.")
    clearAllEntries()

# Function for seeing a list of all the blocked websites in the GUI
def seeAllBlockedWebsites():
    top = Toplevel()
    top.title("All Blocked Websites")
    top.geometry("600x600")

    frame = ttk.Frame(top)
    frame.pack(fill="both",expand=True)

    listOfBlockedWebsites = ttk.Treeview(frame)
    listOfBlockedWebsites['columns'] = ("#","Name","Domain")
    listOfBlockedWebsites.column("#0", width = 0, stretch=NO)
    listOfBlockedWebsites.column("#", width = 120, anchor = W)
    listOfBlockedWebsites.column("Name", width = 120, anchor = W)
    listOfBlockedWebsites.column("Domain", width = 120, anchor = W)
    listOfBlockedWebsites.heading("#0", text="")
    listOfBlockedWebsites.heading("#",text="Index", anchor = W)
    listOfBlockedWebsites.heading("Name",text="Name", anchor = W)
    listOfBlockedWebsites.heading("Domain",text="Domain", anchor = W)
    verticalScrollbar = ttk.Scrollbar(frame, orient="vertical", command=listOfBlockedWebsites.yview)
    verticalScrollbar.pack(side=RIGHT,fill=Y)
    listOfBlockedWebsites.pack(fill = "both", expand = True)
    listOfBlockedWebsites.configure(yscrollcommand=verticalScrollbar.set)

    conn = sqlite3.connect('websites_blocked.db')

    cursor = conn.cursor()

    cursor.execute("SELECT * FROM websites_blocked")
    domain_entries = cursor.fetchall()
    domain_entries = sorted(domain_entries, key=lambda y: y[0])
    for index, domain_entry in enumerate(domain_entries):
        name, domain = domain_entry
        listOfBlockedWebsites.insert(parent='',index='end',iid=index,text="",values=(index + 1,name,domain))

    conn.commit()

    conn.close()

root.mainloop()
