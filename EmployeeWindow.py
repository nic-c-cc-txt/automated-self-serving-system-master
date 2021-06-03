#!/usr/bin/env python3
"""
Programmer: Chris Blanks
Last Edited: 11/3/2018
Project: Automated Self-Serving System
Purpose: This script defines the EmployeeWindow Class.
"""

import tkinter as tk
from tkinter import messagebox
import os

#My Scripts
from AppWindow import AppWindow
from DrinkProfileManager import DrinkProfileManager
from ApplicationUserEditor import ApplicationUserEditor


class EmployeeWindow(AppWindow):
    
    operation_instructions_file_path = """/home/pi/PYTHON_PROJECTS/automated-self-serving-system/system_info/instructions_4_employee.txt"""

    def __init__(self,main_app_instance, isAdminMode = False):
        AppWindow.__init__(self,main_app_instance)
        
        self.master = main_app_instance.employee_top_lvl
        self.master.configure(bg= AppWindow.background_color)
        self.frame = tk.Frame(self.master)
        self.frame.configure(bg= AppWindow.background_color)
        self.size= [self.master.winfo_screenwidth() , self.master.winfo_screenheight() ]
        
        self.parent_menu = tk.Menu(self.frame)
        self.master.config(menu= self.parent_menu)
        self.main_app = main_app_instance
        
        self.isAdminMode = isAdminMode

        self.configureWindow()
        self.frame.grid()
        
        self.createHelpMenu()
        self.displayDrinkOptionsInGUI() #Method from AppWindow

        
    def configureWindow(self):
        """Sets window geometry and limits."""
        self.master.geometry("{0}x{1}+0+0".format(self.master.winfo_screenwidth()
                                                  ,self.master.winfo_screenheight()))   
        self.master.protocol("WM_DELETE_WINDOW",self.deployExitMessageBox)

        if self.isAdminMode:
            self.setupAdminMenuBar()
        else:
            self.setupOptionsMenuBar()


    def setupAdminMenuBar(self):
        """Provides extra features in the menu bar for full control of the app."""
        print("Admin status.")
        self.admin_menu = tk.Menu(self.parent_menu,tearoff=0)
        self.parent_menu.add_cascade(label="Admin Options",menu=self.admin_menu)
        
        self.admin_menu.add_command(label="Launch Drink Profile Manager",command= self.launchDrinkProfileManager)
        self.admin_menu.add_separator()
        self.admin_menu.add_command(label="Display Log" ,command= self.displayLogFile) #allow option to delete them
        self.admin_menu.add_separator()
        self.admin_menu.add_command(label="Edit Configuration" ,command= self.editConfigFile)
        self.admin_menu.add_separator()
        self.admin_menu.add_command(label="Edit User Logins" ,command= self.editUserLogins)
        self.admin_menu.add_separator()
        self.admin_menu.add_command(label="Show IP Address" ,command= self.showIPAddress)
        

    
    def setupOptionsMenuBar(self):
        """Provides regular features in the menu bar for employees"""
        print("Employee status.")
        self.options_menu = tk.Menu(self.parent_menu,tearoff=0)
        self.parent_menu.add_cascade(label="Employee Options",menu= self.options_menu)

        self.options_menu.add_command(label="Launch Drink Profile Manager" ,command= self.launchDrinkProfileManager)


    def launchDrinkProfileManager(self):
        """Allows the employee to add, edit, or delete drink profiles."""
        self.top = tk.Toplevel(self.master)
        self.top.title("Drink Profile Manager")
        self.top.geometry("{0}x{1}+0+0".format(self.master.winfo_screenwidth()
                                                  ,self.master.winfo_screenheight()))
        
        
        profile_manager_win = tk.PanedWindow(self.top,orient= tk.HORIZONTAL)
        profile_manager_win.pack(fill=tk.BOTH,expand=1)
        self.drink_profile_manager = DrinkProfileManager(profile_manager_win
                                                         ,self.main_app,self.isAdminMode,self.size)
        self.master.withdraw()

    
    def displayLogFile(self):
        """Displays the most recent log file."""
        file = open(self.main_app.todays_log,'r')
        lines = file.readlines()
        file.close()
        msg = " ".join(lines)
        
        self.log_display = tk.Toplevel()
        self.log_display.title("Current Log File:")
        #top.geometry("350x230")
        
        scroll = tk.Scrollbar(self.log_display,orient= tk.VERTICAL)
        scroll.grid(row=0,column=1,sticky="ns")
        
        canvas = tk.Canvas(self.log_display,width=600,
                           height=500,
                           scrollregion=(0,0,2000,2000))
        canvas.grid(row=0,column=0,sticky="nsew")

        scroll.config(command=canvas.yview)
        canvas.config(yscrollcommand = scroll.set)
        canvas.create_text((0,0),text=msg,anchor="nw") #top left and anchored to the right

        log_menu = tk.Menu(self.log_display)
        log_options = tk.Menu(log_menu,tearoff=0)
        log_menu.add_cascade(label="Options",menu=log_options)

        self.log_display.config(menu=log_menu)
        
        log_options.add_command(label="Clear Log"
                                    ,command= self.clearTodayLog)
        self.log_display.rowconfigure(0,weight=1)
        self.log_display.columnconfigure(0,weight=1)


    def clearTodayLog(self):
        """Clears the current log."""
        os.remove(self.main_app.todays_log)
        self.deployClearedMessageBox()
        self.main_app.writeToLog("Cleaned log file.")


    def deployClearedMessageBox(self):
        """Deploys the message box for when the log file is cleared."""
        if messagebox.askokcancel("Cleared today's log","press Ok to continue."):
            self.log_display.destroy()


    def editUserLogins(self):
        """Displays current registered users. Allows for adding or deleting users."""
        user_editor_top = tk.Toplevel()
        user_editor_top.title("Application User Editor")
        #user_editor_top.geometry("{0}x{1}+0+0".format(self.size[0],self.size[1]))
        self.user_editor =  ApplicationUserEditor(user_editor_top,self.main_app,self.size)

    
    def editConfigFile(self):
        """Allows editing of the contents in the configuration file. """
        pass #Will be defined at a later time


    def showIPAddress(self):
        """Shows the current IP address in a top level window. """
        ip_window = tk.Toplevel()
        ip_window.title("IP Address")
        ip_address = str(self.main_app.ip_address)
        ip_label = tk.Label(ip_window,text=ip_address,font=("Georgia","20","bold"),fg="red")
        ip_label.grid()

        
    def deployExitMessageBox(self):
        """Destroys employee window and brings up root window."""
        if messagebox.askokcancel("Quit","Are you sure?"):
            self.isAdminMode = False
            self.master.destroy()
            self.main_app.master.deiconify()
