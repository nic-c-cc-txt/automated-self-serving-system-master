#!/usr/bin/env python3
"""
Programmer: Chris Blanks
Last Edited: 11/3/2018
Project: Automated Self-Serving System
Purpose: This script defines the MainApp class that runs everything.
"""

#Standard library imports
import tkinter as tk
import os
import time
import datetime
from threading import Timer
from cryptography.fernet import Fernet
from subprocess import check_output
import subprocess
import _thread as thread
import http.server as hs
import socketserver as ss

#My scripts
from CustomerWindow import CustomerWindow
from EmployeeWindow import EmployeeWindow
import DrinkProfile as dp_class
from LoginWindow import LoginWindow
from KeyboardWindow import KeyboardWindow


def runMainApplication():
    """Basic run of application."""
    print(os.getcwd())
    root = tk.Tk()
    main_app = MainApp(master= root)
    root.mainloop()


class MainApp:

    #class member variables
    isEmployeeMode= False
    isValidLogin = False
    drink_profile_directory = "/home/pi/PYTHON_PROJECTS/automated-self-serving-system/drink_profiles"
    config_file_path = "/home/pi/PYTHON_PROJECTS/automated-self-serving-system/system_info/config.txt"
    user_login_path= "/home/pi/PYTHON_PROJECTS/automated-self-serving-system/system_info/user_login.txt"
    encrypt_key_path = "/home/pi/PYTHON_PROJECTS/automated-self-serving-system/system_info/key.txt"
    system_info = "/home/pi/PYTHON_PROJECTS/automated-self-serving-system/system_info"
    drink_names = []
    isWithoutLogin = False
    
    def __init__(self,master):
        self.master = master

        self.ip_address = self.getIPAddress()
        self.writeToLog("Running main application")
        self.writeToSharedData()
        self.startHTTPThread()
        self.cipher_suite = self.setupUserEncryption()
        
        if self.isWithoutLogin == True:
            self.createDefaultUserLoginFile()
            
        self.drink_objects = self.getDrinks()
        
        self.createMainWindow()
        self.selectWindow()
        
        self.retrieveConfigurationInformation()
        self.cleanOldDrinksFromConfig()
        

    def selectWindow(self):
        """Determines what window is open."""
        #input mode until GPIO pin is setup to trigger employee mode
        selection = int(input("Press 1 to enter employee mode."))

        if selection == 1:
            self.isEmployeeMode = True
            self.launchLoginWindow()           
        else:
            self.isEmployeeMode = False
            self.master.withdraw()
            self.createCustomerWindow()


    def createMainWindow(self):
        """Displays main window elements. """
        self.master.geometry("200x200")
        self.master.geometry("{0}x{1}+0+0".format(self.master.winfo_screenwidth()
                                                  ,self.master.winfo_screenheight()))
        self.main_title = tk.Label(self.master,text="Root Window")
        self.main_title.grid()

        self.customer_window_btn = tk.Button(self.master,text="customer window"
                                             ,command= lambda window="customer": self.relaunchWindow(window))
        self.customer_window_btn.grid()
        self.employee_window_btn = tk.Button(self.master,text="employee window"
                                             ,command= lambda window="employee": self.relaunchWindow(window))
        self.employee_window_btn.grid()

        
    def relaunchWindow(self,window):
        """ Relaunches the selected window."""
        if window == "customer":
            self.isEmployeeMode = False
            self.master.withdraw()
            self.createCustomerWindow()
        elif window == "employee":
            self.isEmployeeMode = True
            self.master.withdraw()
            self.launchLoginWindow()
        else:
            print("What the heck?")

        
    def createCustomerWindow(self):
        """Creates separate customer window."""
        self.customer_top_lvl = tk.Toplevel(self.master)
        self.customer_window = CustomerWindow(self)

        
    def createEmployeeWindow(self,isAdminMode):
        """Creates separate employee window """
        self.employee_top_lvl = tk.Toplevel(self.master)
        self.employee_window = EmployeeWindow(self,isAdminMode)

    
    def launchLoginWindow(self):
        """Launches login window when employee mode is selected."""
        self.login_top_lvl = tk.Toplevel(self.master)
        self.login_window = LoginWindow(self)

        
    def launchKeyboardWindow(self):
        """Launches a top level window that contains a keyboard that can deliver
        input to processes that need it."""
        self.keyboard_top_lvl = tk.Toplevel(self.master)
        self.keyboard_window = KeyboardWindow(self)

        
    def getDrinks(self):
        """Retrieves a list of active Drink objects."""
        temp = []
        self.all_defined_drinks = []
        os.chdir(self.drink_profile_directory)
        drink_profile_names = os.listdir(os.getcwd())
        for name in drink_profile_names:
            path_builder = self.drink_profile_directory +"/"+ name
            os.chdir(path_builder)
            text_file_index = 0
            if ".txt" in os.listdir(os.getcwd())[0]:
                pass
            else:
                text_file_index= 1
                
            drink = dp_class.DrinkProfile(path_builder +"/"+ os.listdir(os.getcwd())[text_file_index])
         
            if drink.isActive == "1":
                drink.name = (drink.name).replace(" ","_")
                drink.addDrinkToConfig()
                temp.append(drink)
            self.all_defined_drinks.append(drink)
        #go back to SENIOR_DESIGN_CODE directory
        os.chdir("..")
        os.chdir("..")
        return temp


    def retrieveConfigurationInformation(self):
        """Retrieves configuration info (e.g. drink names) from config file """
        f = open(self.config_file_path,'r+')
        lines = f.read().splitlines()
        #print("'{}' contents:\n".format((f.name).split("/")[-1]),'\n'.join(lines))

        line_number = 1
        for line in lines:
            if line_number == 1:
                if line.split()[1] == '0':
                    print("Config file is not locked.\n\n")
                else:
                    self.isLocked = True
                    print("Config file is locked.\n\n")
            if line_number == 2:
                drinks = line.split(" ")
                for i in range(len(drinks)-1):
                    self.drink_names.append(drinks[i+1])
            line_number+=1
        f.truncate()    
        f.close()


    def updateConfigurationFile(self,item_to_update,updated_value= None):
        """ """
        f = open(self.config_file_path,"r+")
        lines = f.read().splitlines()
        f.seek(0)

        line_headers = ["locked ","active_drink_list ","system_status "]
        line_to_edit = 0
        
        if item_to_update == "data_lock":
            line_to_edit = 1
        if item_to_update == "drink_list":
            line_to_edit = 2
        if item_to_update == "system_status":
            line_to_edit = 3

        line_number = 1
        for line in lines:
            if line_number == line_to_edit and updated_value != None:
               line = line_headers[line_to_edit - 1] + updated_value
               f.write(line+"\n")
            else:
                f.write(line+"\n")
            if line_number == 3:
                break
            line_number+=1
        f.truncate()
        f.close()


    def cleanOldDrinksFromConfig(self):
        """Updates the active drinks in the config file."""
        cleaned_list_of_names = ""
        loaded_drink_object_names = []
        for drink in self.drink_objects:
            loaded_drink_object_names.append((drink.name).replace("_"," "))
        for config_name in self.drink_names:
            if config_name.replace("_"," ") in loaded_drink_object_names:
                cleaned_list_of_names = cleaned_list_of_names + config_name + " "
        self.updateConfigurationFile("drink_list",cleaned_list_of_names)
        self.writeToLog("Cleaned Config file.")
                
               
    def writeToLog(self, message):
        """Writes messages into the log.txt file."""
        self.todays_log = self.system_info+"/log_files/log_on_"+str(datetime.date.today())+".txt"
        log = open(self.todays_log,"w+")
        full_msg = str(datetime.datetime.now()) +" : " + message
        log.seek(2)
        log.write(full_msg + "\n")
        log.close()


    def writeToDrinkSalesLog(self, message):
        """Writes time-stamped sales info into a log for each day."""
        self.todays_drink_sales = self.system_info+"/drink_sales/drink_sales_"+str(datetime.date.today())+".txt"
        log = open(self.todays_drink_sales,"a")
        full_msg = str(datetime.datetime.now()) +" : " + message
        log.seek(2)
        log.write(full_msg + "\n")
        log.close()

    
    def addUserToLogin(self,user_type,username,password):
        """Creates a new user in the user_login file. Ex: self.addUserToLogin("R","Lei","Zhang")"""
        file = open(self.user_login_path,"rb+")
        lines = file.read().splitlines()
        file.seek(0)
        line_num = 1
        next_line = False
        if user_type == "A":
            for line in lines:
                line = str((self.cipher_suite.decrypt(line)).decode('ASCII'))
                if next_line == True:
                    file.write(temp+b"\n")
                    next_line = False
                if "ADMIN USER" in line:
                    temp = username +" "+ password
                    temp = self.cipher_suite.encrypt(temp.encode(encoding='UTF-8'))
                    next_line = True
                if "END" in line:
                    line = self.cipher_suite.encrypt(line.encode(encoding='UTF-8'))
                    file.write(line+b"\n")
                    break

                line = self.cipher_suite.encrypt(line.encode(encoding='UTF-8'))
                file.write(line+b"\n")
        else:
            for line in lines:
                line = str((self.cipher_suite.decrypt(line)).decode('ASCII'))
                if "REGULAR USER" in line:
                    line = line +"\n"+ username +" "+ password
                if "END" in line:
                    line = self.cipher_suite.encrypt(line.encode(encoding='UTF-8'))
                    file.write(line+b"\n")
                    break

                line = self.cipher_suite.encrypt(line.encode(encoding='UTF-8'))
                file.write(line+b"\n")

        file.flush()
        file.truncate()
        file.close()

        msg = "Added "+username+ " account to login."
        self.writeToLog(msg)        


    def deleteUserFromLogin(self, username, password):
        """Deletes a user in the user_login file (besides the original admin account)."""
        file = open(self.user_login_path,"rb+")
        lines = file.read().splitlines()
        file.seek(0)
        login_combo = username +" " + password
        print(login_combo)
        for line in lines:
            line = str((self.cipher_suite.decrypt(line)).decode('ASCII'))
            print("users "+ line)
            if "END" in line:
                line = self.cipher_suite.encrypt(line.encode(encoding='UTF-8'))
                file.write(line+b"\n")
                break
            if "REGULAR" in line:
                line = self.cipher_suite.encrypt("REGULAR USER".encode(encoding='UTF-8'))
                file.write(line+b"\n")
            elif login_combo not in str(line):
                print("rest:"+str(line) )
                line = self.cipher_suite.encrypt(line.encode(encoding='UTF-8'))
                file.write(line+b"\n")
            else:
                print(line)
                pass
        file.truncate()
        file.flush()
        file.close()

        msg = "Removed "+username+ " account from login."
        self.writeToLog(msg)  


    def setupUserEncryption(self):
        """Creates an encryption key if one is not already made """
        if os.path.exists(self.encrypt_key_path):
            file = open(self.encrypt_key_path,"rb")
            key = file.readline()
            if os.path.exists(self.user_login_path):
                pass
            else:
                self.isWithoutLogin = True
            file.close()
            
        else:
            key = Fernet.generate_key()
            file = open(self.encrypt_key_path,"wb")
            file.write(key)
            file.close()
            self.isWithoutLogin = True

        cipher_suite = Fernet(key)    
        return cipher_suite


    def createDefaultUserLoginFile(self):
        """Creates a default user_login.txt file that has the
        default login credentials in an encrypted form. """
        print("Making new login file.")
        new_user_login = open(self.user_login_path,'wb')
        
        admin_str = "ADMIN USER"
        default_usr_str="admin admin"
        reg_usr_str = "REGULAR USER"
        end_str = "END"
        
        admin_str = self.cipher_suite.encrypt(admin_str.encode(encoding='UTF-8'))
        default_usr_str = self.cipher_suite.encrypt(default_usr_str.encode(encoding='UTF-8'))
        reg_usr_str = self.cipher_suite.encrypt(reg_usr_str.encode(encoding='UTF-8'))
        end_str = self.cipher_suite.encrypt(end_str.encode(encoding='UTF-8'))
        
        new_user_login.write(admin_str+b"\n")
        new_user_login.write(default_usr_str+b"\n")
        new_user_login.write(reg_usr_str+b"\n")
        new_user_login.write(end_str+b"\n")
        
        new_user_login.truncate()
        new_user_login.close()
        self.isWithoutLogin = False
        #self.writeToLog("Made new login file")


    def getIPAddress(self):
        host_info = check_output(['hostname','-I'])
        ip_address = host_info.split()[0].decode('ascii')
        print("IP: "+ip_address)
        return ip_address
    
    def writeToSharedData(self):
        """Updates the write to shared data every 5 minutes."""
        MILLI = 1000
        MIN_IN_SEC = 300   # 300 sec = 5 min
        
        now = time.strftime("%H:%M:%S")
        print(now) #keeps track of write time
        
        self.todays_shared_data= self.system_info+"/shared_data/shared_data_"+str(datetime.date.today())+".txt"
        log = open(self.todays_shared_data,"w")
        msg = """STATUS
idle
employee
chris
INVENTORY
rum 500 1000
vodka 500 1000
tequila 600 1000
gin 1000 1000
triple_sec 300 400
soda_water 200 1500
SALES
cuba_libre 55.00
daiquiri 10.00
kamikaze 0.00
long_island_iced_tea 23.00
naval_gimlet 5.00
rum_and_coke 10.00
screwdriver 20.00
tequila 0.00
vodka 100.00
vodka_and_cranberry 40.00"""
        log.write(msg)
        log.truncate()
        log.close()
        
        self.master.after(MIN_IN_SEC*MILLI,self.writeToSharedData) #recursively writes to shared data every 5 minutes


    def startHTTPThread(self):
        """Creates a http server in a separate thread from the GUI."""
        thread.start_new_thread(self.startHTTPServer,tuple())


    def startHTTPServer(self):
        """Opens a http server in the shared data directory."""
        try:
            os.chdir("/home/pi/PYTHON_PROJECTS/automated-self-serving-system/system_info/shared_data")
            subprocess.call(["python", "-m", "SimpleHTTPServer"," 8000"])
        except PermissionError as err:
            print("Port is already open.") #printed in the abyss

        os.chdir("..")
        os.chdir("..")
        
    
if __name__ == "__main__":
    runMainApplication()
