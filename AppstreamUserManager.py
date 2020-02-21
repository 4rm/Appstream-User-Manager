import os
import sys
import time
import boto3
import keyring
import requests
import webbrowser
import tkinter as tk
from tkinter import ttk
from pandas import read_csv
from tkinter import filedialog
from botocore.config import Config
from keyring.backends import Windows
from tkinter.scrolledtext import ScrolledText

class MainApplication(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.parent = parent

        self.local_version=2.0

        try:
            #Check if there's an updated version
            r=requests.get(url="https://api.github.com/repos/4rm/Appstream-User-Manager/releases/latest").json()

            web_version=float(r['tag_name'][1:])

            def download():
                webbrowser.open('https://github.com/4rm/Appstream-User-Manager/releases')
                available_update.destroy()

            if web_version > self.local_version:
                available_update=tk.Toplevel()
                if "nt" == os.name:
                    available_update.iconbitmap(self.resource_path('images/icon.ico'))
                available_update.wm_title('Updates are available')
                info_frame=tk.Frame(available_update)
                info_frame.pack(padx=10, pady=10)
                message=tk.Label(info_frame, text="New update is available: "
                                 + r['tag_name'],
                                 font=(None,14))
                message.pack()
                yours=tk.Label(info_frame, text="Your version: v"
                               + str(self.local_version),
                               font=(None, 9),
                               foreground="red")
                yours.pack()
                update_info=ScrolledText(info_frame, height=8, width=60)
                update_info.insert(tk.END, r['body'])
                update_info.config(state=tk.DISABLED)
                update_info.pack(pady=(0,10))
                button_frame=tk.Frame(info_frame)
                button_frame.pack()
                Download_button=tk.Button(button_frame, text="Download",
                                          command=lambda:download())
                Download_button.pack(side=tk.LEFT, padx=(0,10))
                Later_button=tk.Button(button_frame, text="Maybe later",
                                       command=lambda:available_update.destroy())
                Later_button.pack(side=tk.LEFT)
                                          
                available_update.attributes('-topmost', 1)
                available_update.lift()
                root.wait_window(available_update)
        except Exception as e:
            print(e)

        root.title("Appstream User Manager")
        if "nt" == os.name:
            root.iconbitmap(self.resource_path('images/icon.ico'))

        self.popup=tk.Toplevel()
        if "nt" == os.name:
            self.popup.iconbitmap(self.resource_path('images/icon.ico'))
        
        self.credentials_frame=CredentialsFrame(self)
        self.credentials_frame.pack()

        self.client=None
        
        self.user_list=[]
        self.stacks=[]
        self.selected_users=[]
        self.roster=[]
        
        self.main_frame=MainFrame(self)
        self.main_frame.pack(side="right", fill="y")

        self.holding_frame=None

    def GetUserList(self,*args):
        if self.client is not None:
            if len(args):
                #If a NextToken was passed as an argument, use it to get the next page
                user_page=self.client.describe_users(AuthenticationType='USERPOOL', NextToken=args[0])
            else:
                user_page=self.client.describe_users(AuthenticationType='USERPOOL')
            for user_info in user_page['Users']:
                user={"FirstName":  user_info['FirstName'],
                      "LastName":  user_info['LastName'],
                      "UserName": user_info['UserName'],
                      "Status": user_info['Status'],
                      "Enabled": user_info['Enabled'],
                      "Selected": 0,
                      "Widget": None,
                      "Stacks":[]}
                self.user_list.append(user)
            try:
                load=tk.Label(self.holding_frame, text="Loading Users: "+str(len(self.user_list)))
                load.pack(anchor=tk.N)
                self.holding_frame.update()
            except Exception as e:
                print(e)
            if 'NextToken' in user_page:
                load.destroy()
                self.GetUserList(user_page['NextToken'],self.holding_frame)
            else:
                load.destroy()

    def GetStacks(self):
        #Get two variables per stack, for the Manage and Add frame
        if self.client is not None:
            for stack in self.client.describe_stacks()['Stacks']:
                var=tk.IntVar()
                var2=tk.IntVar()
                self.stacks.append({"Name":stack['Name'],
                                    "var":var,
                                    "var2":var2})

    def resource_path(self, relative_path):
        #Get absolute path to resource, works for dev and for
        #PyInstaller - Found on stackoverflow
        try:
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath('.')
        return os.path.join(base_path, relative_path)
        
class CredentialsFrame(tk.Frame):
    def __init__(self, parent):
        tk.Frame.__init__(self, parent)
        self.parent = parent

        def login(popup):
            try:
                self.blank_warning.destroy()
                self.login_warning.destroy()
            except Exception as e:
                print(e)
                
            self.blank_warning=tk.Label(popup, text="Fields cannot be left blank",  foreground="red")
            
            if not all((access_key.get(), secret_key.get(), region_key.get())):
                #No field can be left blank
                self.blank_warning.pack()
                return
            
            #Create a "test_client" object to verify keys
            test_client = boto3.client('appstream', 
                aws_access_key_id=access_key.get(),
                aws_secret_access_key=secret_key.get(),
                region_name=region_key.get()
            )

            try:
                test_client.describe_directory_configs()
            except Exception as e:
                self.login_warning=tk.Label(popup, text=e, foreground="red", wraplength=325)
                self.login_warning.pack(pady=(0,5))
                return

            #Batch jobs lend themselves to rate limiting
            #increase the number of allowed tries
            #AWS already implements exponential backoff
            config=Config(retries=dict(max_attempts=20))
            
            parent.client = boto3.client('appstream', 
                aws_access_key_id=access_key.get(),
                aws_secret_access_key=secret_key.get(),
                region_name=region_key.get(),
                config=config
            )

            #Write the keys to the OS keyring, if wanted
            if remember_me.get()==1:
                keyring.set_password("Appstream_User_Manager", "Access Key", access_key.get())
                keyring.set_password("Appstream_User_Manager", "Secret Access Key", secret_key.get())
            elif remember_me.get()==0:
                try:
                    keyring.delete_password("Appstream_User_Manager", "Access Key")
                    keyring.delete_password("Appstream_User_Manager", "Secret Access Key")
                except Exception as e:
                    print(e)
            root.lift()
            popup.destroy()
        
        #popup defined in MainApplication
        parent.popup.wm_title("Enter Credentials")
        parent.popup.attributes('-topmost', 1)
        parent.popup.lift()

        data_frame=tk.Frame(parent.popup)
        data_frame.pack(side=tk.TOP, padx=10, pady=10)
        
        label_frame=tk.Frame(data_frame)
        label_frame.pack(side=tk.LEFT, padx=(0,5))

        entry_frame=tk.Frame(data_frame)
        entry_frame.pack(side=tk.RIGHT)

        keyring.set_keyring(Windows.WinVaultKeyring())
        
        access_label=ttk.Label(label_frame, text="Access Key ID:")
        access_label.pack(side="top", fill=tk.X)
        access_key=tk.Entry(entry_frame)
        access_key.pack(fill=tk.X)
        
        secret_label=ttk.Label(label_frame, text="Secret Access Key:")
        secret_label.pack(side="top", fill=tk.X)
        secret_key=tk.Entry(entry_frame)
        secret_key.pack(fill=tk.X)

        region_label=ttk.Label(label_frame, text="Region:")
        region_label.pack(side="top", fill=tk.X)
        region_key=tk.Entry(entry_frame, width=42)
        region_key.insert(tk.END, "us-east-1")
        region_key.pack(fill=tk.X)

        button_frame=tk.Frame(parent.popup)
        button_frame.pack(side=tk.BOTTOM, anchor=tk.S, pady=(0,5))
        B1=ttk.Button(button_frame, text="Okay", command = lambda:login(parent.popup))
        B1.pack(side=tk.LEFT)
        remember_me=tk.IntVar()
        save_check=tk.Checkbutton(button_frame, text="Remember me", variable=remember_me)
        save_check.pack(side=tk.LEFT)

        try:
            access_key.insert(tk.END, keyring.get_password("Appstream_User_Manager", "Access Key"))
            secret_key.insert(tk.END, keyring.get_password("Appstream_User_Manager", "Secret Access Key"))
        except Exception as e:
            print(e)
        else:
            save_check.select()

class MainFrame(tk.Frame):
    def __init__(self, parent):
        tk.Frame.__init__(self, parent)
        self.parent = parent
        
        def on_configure(event,canvase):
            canvase.configure(scrollregion=canvase.bbox('all'))

        def _on_mousewheel(event,canvase):
            canvase.bind_all("<MouseWheel>", lambda event:mousewheel(event,canvase))

        def _off_mousewheel(event,canvase):
            canvase.unbind_all("<MouseWheel>")

        def mousewheel(event,canvase):
            canvase.yview_scroll(int(-1*(event.delta/120)), "units")

        def click(event,i):
            def resend(uname):
                try:
                    try:
                        fail.destroy()
                    except:
                        None
                    parent.client.create_user(UserName=uname, MessageAction="RESEND",AuthenticationType="USERPOOL")
                except Exception as e:
                    fail=tk.Label(button_frame, text=e, foreground="red")
                    fail.pack(side=tk.LEFT)
                else:
                    passed=tk.Label(button_frame, text="Sent!", foreground="green")
                    passed.pack(side=tk.LEFT)
                    passed.after(2000,passed.destroy)
                    
            user_index=list(filter(lambda x: x[1]['UserName']==i['UserName'],enumerate(parent.user_list)))[0][0]
            parent.user_list[user_index]['Stacks']=[]
            for stack in parent.client.describe_user_stack_associations(UserName=i['UserName'],AuthenticationType="USERPOOL")['UserStackAssociations']:
                parent.user_list[user_index]['Stacks'].append(stack['StackName'])
            if parent.user_list[user_index]['Selected']==0:
                name=tk.Frame(self.user_info_frame)
                name.pack(fill=tk.X, expand=True)
                info_user=tk.Label(name, text="Username: "+i['UserName'], highlightthickness=0, borderwidth=0)
                info_user.pack(anchor=tk.W)
                info_name=tk.Label(name, text="Name: "+i['FirstName']+' '+i['LastName'], highlightthickness=0, borderwidth=0)
                info_name.pack(anchor=tk.W)

                s=", "
                s=s.join(i['Stacks'])
                
                info_stacks=tk.Label(name, text="Stacks: "+s, highlightthickness=0, borderwidth=0, wraplength=220, justify=tk.LEFT)
                info_stacks.pack(anchor=tk.W)

                button_frame=tk.Frame(name)
                button_frame.pack(anchor=tk.W, pady=2)
                resend_button=tk.Button(button_frame, text="Resend welcome email",
                                        relief=tk.GROOVE,
                                        font=(None, 8),
                                        command=lambda username=i['UserName']:resend(username),
                                        cursor="hand2")
                resend_button.pack(side=tk.LEFT)

                if (i['Status'] == 'CONFIRMED'):
                    resend_button.configure(state=tk.DISABLED,
                                            cursor='')
                    
                border=tk.Frame(name, highlightthickness=1, highlightbackground="black", width=220)
                border.pack(fill=tk.X, expand=True, pady=5, side=tk.BOTTOM)
                
                parent.user_list[user_index]['Widget']=name
                event.widget.configure(background="powder blue")
                parent.user_list[user_index]['Selected']=1
                parent.selected_users.append(i)
            elif parent.user_list[user_index]['Selected']==1:
                event.widget.configure(background="SystemButtonFace")
                parent.user_list[user_index]['Selected']=0
                parent.user_list[user_index]['Widget'].pack_forget()
                parent.selected_users.remove(i)
            if len(parent.selected_users)>0:
                self.no_user.pack_forget()
            elif len(parent.selected_users)==0:
                self.no_user.pack()
            self.user_info_canvas.yview_moveto(1)
            
        self.user_canvas_name=None
        self.user_scrollbar_name=None
        def search(search, users):
            for user in parent.selected_users:
                user['Widget'].destroy()
                user['Selected']=0
                parent.selected_users=[]
            self.user_canvas_name.destroy()
            self.user_scrollbar_name.destroy()
            w=tk.Canvas(user_pane)
            w.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            self.user_canvas_name=w
            y=tk.Scrollbar(user_pane, command=w.yview)
            y.pack(side=tk.LEFT, fill='y')
            self.user_scrollbar_name=y

            w.configure(yscrollcommand=y.set)

            f=tk.Frame(w)
            canvas_frame=w.create_window((0,0), window=f, anchor='nw')
            f.bind('<Configure>', lambda event:on_configure(event,w))
            f.bind("<Enter>", lambda event:_on_mousewheel(event,w))
            f.bind("<Leave>", lambda event:_off_mousewheel(event,w))

            if len(search)>0:
                for u in users:
                    try:
                        name_data=u['FirstName']+' '+u['LastName']+' '+u['UserName']
                        if search.lower() in name_data.lower():
                            p=tk.Canvas(f,width=500, height=17,highlightthickness=0)
                            p.pack()
                            p.create_text(3,0,text=u['FirstName'],anchor=tk.NW)
                            p.create_text(150,0,text=u['LastName'],anchor=tk.NW)
                            p.create_text(295,0,text=u['UserName'],anchor=tk.NW)
                            p.bind("<1>", lambda event,u=u:click(event,u))
                    except:
                        None
            elif len(search)==0:
                for u in users:
                    p=tk.Canvas(f,width=500, height=17,highlightthickness=0)
                    p.pack()
                    p.create_text(3,0,text=u['FirstName'],anchor=tk.NW)
                    p.create_text(150,0,text=u['LastName'],anchor=tk.NW)
                    p.create_text(295,0,text=u['UserName'],anchor=tk.NW)
                    p.bind("<1>", lambda event,u=u:click(event,u))
                  
        def stack_apply(mode):
            def yeah():
                for user in parent.selected_users:
                    for stack in parent.stacks:
                        if mode=='set':
                            if stack['var'].get()==1 and stack['Name'] not in user['Stacks']:
                                parent.client.batch_associate_user_stack(UserStackAssociations=[{
                                    'StackName':stack['Name'],
                                    'UserName':user['UserName'],
                                    'AuthenticationType':"USERPOOL",
                                    'SendEmailNotification':bool(email.get())
                                    }])
                            if stack['var'].get()==0 and stack['Name'] in user['Stacks']:
                                parent.client.batch_disassociate_user_stack(UserStackAssociations=[{
                                    'StackName':stack['Name'],
                                    'UserName':user['UserName'],
                                    'AuthenticationType':"USERPOOL",
                                    'SendEmailNotification':bool(email.get())
                                    }])
                        elif mode=='add':
                            parent.client.batch_associate_user_stack(UserStackAssociations=[{
                                'StackName':stack['Name'],
                                'UserName':user['UserName'],
                                'AuthenticationType':"USERPOOL",
                                'SendEmailNotification':bool(email.get())
                                }])
                        elif mode=='remove':
                                parent.client.batch_disassociate_user_stack(UserStackAssociations=[{
                                'StackName':stack['Name'],
                                'UserName':user['UserName'],
                                'AuthenticationType':"USERPOOL",
                                'SendEmailNotification':bool(email.get())
                                }])
                search('',parent.user_list)
                for stack in parent.stacks:
                    stack['var'].set(0)
                confirm.destroy()
            def no():
                confirm.destroy()
            confirm=tk.Toplevel()
            confirm.attributes('-topmost', 1)
            confirm.wm_title("Confirm Changes")
            if "nt" == os.name:
                confirm.iconbitmap(parent.resource_path('images/icon.ico'))
            confirm.lift()
            yes=tk.Label(confirm, text="Would you like to make the following changes?")
            yes.pack(side=tk.TOP, anchor=tk.W, padx=5, pady=5)

            info_frame=tk.Frame(confirm)
            info_frame.pack(anchor=tk.W, padx=5)
            user_frame=tk.Frame(info_frame)
            user_frame.pack(side=tk.LEFT, anchor=tk.N)
            user_label=tk.Label(user_frame, text="Users", font=(None,  9, 'bold'))
            user_label.pack()
            for user in parent.selected_users:
                u=tk.Label(user_frame, text=user['FirstName']+' '+user['LastName'] +' ('+user['UserName']+')')
                u.pack(anchor=tk.W)
                
            border_frame=tk.Frame(info_frame, highlightthickness=3, highlightbackground="gray75")
            border_frame.pack(fill=tk.Y,padx=5,expand=True,anchor=tk.W, side=tk.LEFT)
            
            stack_frame=tk.Frame(info_frame)
            stack_frame.pack(side=tk.RIGHT,anchor=tk.N)
            stack_label_header=tk.Label(stack_frame, text="Stacks", font=(None, 9, 'bold'))
            stack_label_header.pack()
            for stack in parent.stacks:
                ind_stack_frame=tk.Frame(stack_frame)
                ind_stack_frame.pack(anchor=tk.W)
                if mode=='set':
                    stack_label=tk.Label(ind_stack_frame, text=stack['Name'])
                    stack_label.pack(side=tk.RIGHT)
                    if stack['var'].get()==1:
                        check=tk.Label(ind_stack_frame, text=u'\u2713', foreground="green")
                        check.pack(side=tk.LEFT)
                    elif stack['var'].get()==0:
                        cross=tk.Label(ind_stack_frame,  text=u'\u2717', foreground='red')
                        cross.pack(side=tk.LEFT)
                elif mode=='add':
                    if stack['var'].get()==1 and stack['Name'] not in user['Stacks']:
                        stack_label=tk.Label(ind_stack_frame, text=stack['Name'])
                        stack_label.pack(side=tk.RIGHT)
                        check=tk.Label(ind_stack_frame, text=u'\u2713', foreground="green")
                        check.pack(side=tk.LEFT)
                elif mode=='remove':
                    if stack['var'].get()==1 and stack['Name'] in user['Stacks']:
                        stack_label=tk.Label(ind_stack_frame, text=stack['Name'])
                        stack_label.pack(side=tk.RIGHT)
                        cross=tk.Label(ind_stack_frame,  text=u'\u2717', foreground='red')
                        cross.pack(side=tk.LEFT)
            confirm.update()
            button_frame=tk.Frame(confirm)
            button_frame.pack(side=tk.BOTTOM,pady=(10,5))
            email=tk.IntVar()
            send_email=tk.Checkbutton(button_frame, text="Send email notification?",var=email)
            send_email.pack(side=tk.TOP)
            confirm_button=tk.Button(button_frame, text='Apply', command=lambda:yeah(), width=10)
            confirm_button.pack(side=tk.RIGHT)
            cancel_button=tk.Button(button_frame, text='Cancel', command=lambda:no(), width=10)
            cancel_button.pack(side=tk.LEFT)
            
        def reload():
            parent.user_list=[]
            parent.GetUserList()
            search('',parent.user_list)

        def bulk_resend_welcome():
            bulk_mail_popup=tk.Toplevel()
            bulk_mail_popup.attributes('-topmost', 1)
            bulk_mail_popup.wm_title("Sending emails")
            if "nt" == os.name:
                bulk_mail_popup.iconbitmap(parent.resource_path('images/icon.ico'))
            bulk_mail_popup.lift()

            bulk_mail_progress_frame=tk.Frame(bulk_mail_popup)
            bulk_mail_progress_frame.pack()

            bulk_mail_canvas=tk.Canvas(bulk_mail_progress_frame)
        
            bulk_mail_scrollbar=tk.Scrollbar(bulk_mail_progress_frame,
                                             command=bulk_mail_canvas.yview)
            bulk_mail_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

            bulk_mail_xscrollbar=tk.Scrollbar(bulk_mail_progress_frame,
                                              command=bulk_mail_canvas.xview,
                                              orient=tk.HORIZONTAL)
            bulk_mail_xscrollbar.pack(side=tk.BOTTOM, fill=tk.X)

            bulk_mail_canvas.configure(yscrollcommand=bulk_mail_scrollbar.set)
            bulk_mail_canvas.configure(xscrollcommand=bulk_mail_xscrollbar.set)

            bulk_mail_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

            bulk_mail_frame=tk.Frame(bulk_mail_canvas)
            bulk_mail_canvas_frame=bulk_mail_canvas.create_window((0,0), window=bulk_mail_frame, anchor=tk.NW)
            bulk_mail_frame.bind('<Configure>', lambda event:on_configure(event,bulk_mail_canvas))
            bulk_mail_canvas.bind('<Enter>', lambda event:_on_mousewheel(event,bulk_mail_canvas))
            bulk_mail_canvas.bind('<Leave>', lambda event:_off_mousewheel(event,bulk_mail_canvas))

            errors=0
            successes=0
            disabled=0

            for user in parent.user_list:
                if user['Status'] == 'FORCE_CHANGE_PASSWORD':
                    account=tk.Frame(bulk_mail_frame)
                    account.pack(anchor=tk.W)
                    sent=tk.Label(account, text=user['UserName']+' - ')
                    sent.pack(side=tk.LEFT)
                    if user['Enabled'] is True:
                        try:
                            parent.client.create_user(UserName=user['UserName'],
                                                      MessageAction="RESEND",
                                                      AuthenticationType="USERPOOL")
                        except Exception as e:
                            error=tk.Label(account, text=str(e), foreground='red')
                            error.pack(side=tk.LEFT)
                            errors+=1
                        else:
                            success=tk.Label(account, text="Sent successfully",
                                             foreground="green")
                            success.pack(anchor=tk.W)
                            successes+=1
                    if user['Enabled'] is False:
                        disable=tk.Label(account, text=user['UserName']
                                         +' is disabled',
                                         foreground='red')
                        disable.pack(side=tk.LEFT)
                        disabled+=1
                bulk_mail_canvas.update()
                bulk_mail_canvas.yview_moveto(1)
                time.sleep(1)
            mail_results_frame=tk.Frame(bulk_mail_popup)
            mail_results_frame.pack(side=tk.BOTTOM)
            results=tk.Label(mail_results_frame, text=str(successes)
                             + ' account(s) removed successfully.\n'
                             + str(errors) + ' error(s).\n'
                             + str(disabled) + ' account(s) disabled')
            results.pack()
            okay_button=tk.Button(mail_results_frame, text="Okay",
                                  command=lambda:bulk_mail_popup.destroy(),
                                  width=10)
            okay_button.pack(pady=5)
            mail_results_frame.update()
            
        #Initial window creation

        n=ttk.Notebook(root)
        n.pack_propagate(0)
        n.pack(fill=tk.BOTH, expand=True)
        f1=tk.Frame(n)
        f2=tk.Frame(n)
        f3=tk.Frame(n)
        n.add(f1, text="Manage")
        n.add(f2, text="Add")
        n.add(f3, text="Remove")

        def about_info():
            about_popup=tk.Toplevel()
            about_popup.attributes('-topmost', 1)
            about_popup.wm_title("About")
            if "nt" == os.name:
                about_popup.iconbitmap(parent.resource_path('images/icon.ico'))
            about_popup.lift()
            program_name=tk.Label(about_popup, text="Appstream User Manager v"+str(parent.local_version),font=(None,14))
            program_name.pack()
            logo_canvas=tk.Canvas(about_popup, width=300, height=180)
            logo_canvas.pack()
            self.logo=tk.PhotoImage(file=parent.resource_path('images/icon.gif'))
            logo_canvas.create_image(150, 90, image=self.logo)
            tagline=tk.Label(about_popup, text="Developed by Emilio Garcia\n2020\nIf the code works, don't question it")
            tagline.pack(pady=0)
            github=tk.Label(about_popup, text="Usage help and documentation",
                            fg='blue', font=(None, -12, 'underline'),
                            cursor='hand2')
            github.pack(pady=(10,15))
            github.bind("<1>", lambda event:webbrowser.open('https://github.com/4rm/Appstream-User-Manager'))
            

        about=tk.Label(n, text='?', cursor="hand2")
        about.pack(side=tk.RIGHT, anchor=tk.N)
        about.bind("<1>", lambda event:about_info())

        #Manage tab, pre-login
        user_pane=tk.Frame(f1)
        user_pane.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        parent.holding_frame=user_pane
        
        search_pane=tk.Frame(user_pane)
        search_pane.pack(anchor=tk.N, fill=tk.X)
        search_field=tk.Entry(search_pane, font=(None, 12))
        search_field.pack(side=tk.LEFT, anchor=tk.N, fill=tk.BOTH, expand=True)
        
        self.refrsh=tk.PhotoImage(file=parent.resource_path('images/refresh.gif'))
        self.refrsh=self.refrsh.subsample(3,3)
        reload_button=tk.Button(search_pane,
                                image=self.refrsh,
                                command=lambda:reload(),
                                width=20, height=20)
        reload_button.pack(side=tk.RIGHT, anchor=tk.N)

        self.srch_img=tk.PhotoImage(file=parent.resource_path('images/search.gif'))
        self.srch_img=self.srch_img.subsample(3,3)
        search_button=tk.Button(search_pane,
                                image=self.srch_img,
                                width=20, height=20)
        search_button.pack(side=tk.RIGHT, anchor=tk.N)

        header_pane=tk.Frame(user_pane)
        header_pane.pack(fill=tk.X, padx=(1,0))
        first_name=tk.Label(header_pane, text="First Name", anchor=tk.W, width=20, font=(None, 9, 'bold'))
        first_name.pack(anchor=tk.W, side=tk.LEFT, fill=tk.X)
        last_name=tk.Label(header_pane, text="Last Name", anchor=tk.W, width=20, font=(None, 9, 'bold'))
        last_name.pack(anchor=tk.W, side=tk.LEFT, fill=tk.X)
        user_name=tk.Label(header_pane, text="Username", anchor=tk.W, width=26, font=(None, 9, 'bold'))
        user_name.pack(anchor=tk.W, side=tk.LEFT, fill=tk.X)

        style=ttk.Style()
        style.configure("TLabelframe.Label", foreground="#3d5ebb")

        control_pane=tk.Frame(f1)
        control_pane.pack(side=tk.RIGHT, fill=tk.Y)
        stacks_frame=ttk.Labelframe(control_pane, text='Stacks')
        stacks_frame.pack(fill=tk.X)
        
        stacks_warning=tk.Label(stacks_frame, text="Stacks uninitialized")
        stacks_warning.pack(side="top", fill="x")

        stacks_buttons=tk.Frame(stacks_frame)
        stacks_buttons.pack(side=tk.BOTTOM, fill=tk.X, expand=True)
        stacks_apply=tk.Button(stacks_buttons, text="Set",command=lambda:stack_apply("set"), width=10)
        stacks_apply.pack(anchor=tk.SW, side=tk.LEFT)
        stacks_add=tk.Button(stacks_buttons, text="Add",command=lambda:stack_apply("add"), width=10)
        stacks_add.pack(anchor=tk.SW, side=tk.LEFT)
        stacks_remove=tk.Button(stacks_buttons, text="Remove",command=lambda:stack_apply("remove"), width=10)
        stacks_remove.pack(anchor=tk.SW, side=tk.LEFT)

        bulk_resend=ttk.Labelframe(control_pane, text="Bulk resend")
        bulk_resend.pack(side=tk.TOP, fill=tk.X, anchor=tk.N)
        bulk_resend_button=tk.Button(bulk_resend,
                                     text="Send welcome to unactivated accounts",
                                     height=2,
                                     command=lambda:bulk_resend_welcome())
        bulk_resend_button.pack(fill=tk.X)

        self.user_info_pane=ttk.Labelframe(control_pane, text="User info")
        self.user_info_pane.pack(side=tk.TOP, fill=tk.Y, anchor=tk.N, expand=True)

        self.user_info_canvas=tk.Canvas(self.user_info_pane, width=220)

        self.user_info_yscrollbar=tk.Scrollbar(self.user_info_pane, command=self.user_info_canvas.yview)
        self.user_info_yscrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.user_info_xscrollbar=tk.Scrollbar(self.user_info_pane, orient=tk.HORIZONTAL,
                                               command=self.user_info_canvas.xview)
        self.user_info_xscrollbar.pack(side=tk.BOTTOM, fill=tk.X)

        self.user_info_canvas.configure(yscrollcommand=self.user_info_yscrollbar.set)
        self.user_info_canvas.configure(xscrollcommand=self.user_info_xscrollbar.set)

        self.user_info_canvas.pack(side=tk.LEFT, anchor=tk.N, fill=tk.Y, expand=True)

        self.user_info_frame=tk.Frame(self.user_info_canvas)
        self.user_info_canvas_frame=self.user_info_canvas.create_window((0,0),
                                                                        window=self.user_info_frame,
                                                                        anchor='nw')
        self.user_info_frame.bind('<Configure>', lambda event:on_configure(event,self.user_info_canvas))
        self.user_info_frame.bind("<Enter>", lambda event:_on_mousewheel(event,self.user_info_canvas))
        self.user_info_frame.bind("<Leave>", lambda event:_off_mousewheel(event, self.user_info_canvas))
        

        self.no_user=tk.Label(self.user_info_frame, text="No user selected")
        self.no_user.pack()

        #Add tab
        def add_user():
            if add_individual.get()==1:
                try:
                    parent.client.create_user(UserName=add_individual_UserName_entry.get(),
                                              FirstName=add_individual_FirstName_entry.get(),
                                              LastName=add_individual_LastName_entry.get(),
                                              AuthenticationType="USERPOOL")
                except Exception as e:
                    error=tk.Toplevel()
                    error.attributes('-topmost', 1)
                    error.wm_title("Error")
                    if "nt" == os.name:
                        error.iconbitmap(parent.resource_path('images/icon.ico'))
                    error.lift()
                    error_label=tk.Label(error, text=e, foreground='red')
                    error_label.pack()
                    okay_button=tk.Button(error, text="Okay", command=lambda:error.destroy())
                    okay_button.pack(anchor=tk.CENTER)
                else:
                    time.sleep(2)
                    errors=[]
                    for stack in parent.stacks:
                        if stack['var2'].get()==1:
                            try:
                                parent.client.batch_associate_user_stack(UserStackAssociations=[{
                                    'StackName':stack['Name'],
                                    'UserName':add_individual_UserName_entry.get(),
                                    'AuthenticationType':"USERPOOL",
                                    'SendEmailNotification':True
                                    }])
                                stack['var2'].set(0)
                            except Exception as e:
                                errors.append(e)
                    if len(errors)>0:
                        stack_error=tk.Toplevel()
                        stack_error.attributes('-topmost', 1)
                        stack_error.wm_title("Error")
                        if "nt" == os.name:
                            stack_error.iconbitmap(parent.resource_path('images/icon.ico'))
                        stack_error.lift()
                        stack_error_label=tk.Label(stack_error, text=errors, foreground='red')
                        stack_error_label.pack()
                        stack_okay_button=tk.Button(stack_error, text="Okay", command=lambda:stack_error.destroy())
                        stack_okay_button.pack(anchor=tk.CENTER)
                    else:
                        success=tk.Toplevel()
                        success.attributes('-topmost', 1)
                        success.wm_title("Success")
                        if "nt" == os.name:
                            success.iconbitmap(parent.resource_path('images/icon.ico'))
                        success.lift()
                        success_label=tk.Label(success,
                                               text=add_individual_UserName_entry.get()+" added successfully"
                                               )
                        success_label.pack()
                        success_okay_button=tk.Button(success, text="Okay", command=lambda:success.destroy())
                        success_okay_button.pack(anchor=tk.CENTER)
                            
                    add_individual_LastName_entry.delete(0, tk.END)
                    add_individual_UserName_entry.delete(0, tk.END)
                    add_individual_FirstName_entry.delete(0, tk.END)
                    reload()
            elif add_roster.get()==1:
                try:
                    add_roster_success_popup=tk.Toplevel()
                    add_roster_success_popup.attributes('-topmost', 1)
                    add_roster_success_popup.wm_title("Results")
                    if "nt" == os.name:
                        add_roster_success_popup.iconbitmap(parent.resource_path('images/icon.ico'))
                    add_roster_success_popup.lift()

                    add_roster_progress_frame=tk.Frame(add_roster_success_popup)
                    add_roster_progress_frame.pack()
                    
                    add_roster_canvas=tk.Canvas(add_roster_progress_frame)

                    add_roster_scrollbar=tk.Scrollbar(add_roster_progress_frame, command=add_roster_canvas.yview)
                    add_roster_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

                    add_rosterx_scrollbar=tk.Scrollbar(add_roster_progress_frame, command=add_roster_canvas.xview, orient=tk.HORIZONTAL)
                    add_rosterx_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

                    add_roster_canvas.configure(yscrollcommand=add_roster_scrollbar.set)
                    add_roster_canvas.configure(xscrollcommand=add_rosterx_scrollbar.set)

                    add_roster_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

                    add_roster_frame=tk.Frame(add_roster_canvas)
                    add_roster_canvas_frame=add_roster_canvas.create_window((0,0), window=add_roster_frame, anchor='nw')
                    add_roster_frame.bind('<Configure>', lambda event:on_configure(event,add_roster_canvas))
                    add_roster_canvas.bind("<Enter>", lambda event:_on_mousewheel(event,add_roster_canvas))
                    add_roster_canvas.bind("<Leave>", lambda event:_off_mousewheel(event,add_roster_canvas))

                    errors=0
                    successes=0

                    new_accounts=[]
                    
                    for student in parent.roster:
                        account=tk.Frame(add_roster_frame)
                        account.pack(anchor=tk.W)
                        added=tk.Label(account, text=student['User Name']+' - ')
                        added.pack(side=tk.LEFT, anchor=tk.N)
                        try:
                            parent.client.create_user(UserName=student['User Name'],
                                                      FirstName=student['First Name'],
                                                      LastName=student['Last Name'],
                                                      AuthenticationType="USERPOOL"
                                                      )
                        except Exception as e:
                            print(e)
                            added_roster_account=tk.Label(account, text=str(e), foreground='red')
                            added_roster_account.pack(side=tk.LEFT)
                            errors+=1
                        else:
                            added_roster_account=tk.Label(account, text="Account added successfully",
                                                          foreground="green",
                                                          justify=tk.LEFT)
                            added_roster_account.pack(anchor=tk.N)
                            successes+=1
                        new_accounts.append(added_roster_account)
                        add_roster_canvas.update()
                        add_roster_canvas.yview_moveto(1)
                        time.sleep(1)
                    for stack in parent.stacks:
                        add_roster_canvas.yview_moveto(0)
                        if stack['var2'].get()==1:
                            for i,student in enumerate(parent.roster):
                                current_message=new_accounts[i].cget('text')
                                try:
                                    parent.client.batch_associate_user_stack(UserStackAssociations=[{
                                        'StackName':stack['Name'],
                                        'UserName':student['User Name'],
                                        'AuthenticationType':"USERPOOL",
                                        'SendEmailNotification':True
                                        }])
                                except Exception as e:
                                    print(e)
                                    errors+=1
                                else:
                                    new_accounts[i].configure(text=current_message
                                                                   +'\n'+stack['Name']
                                                                   +' added')
                                    successes+=1
                                add_roster_canvas.yview_moveto(float(i/len(new_accounts)))
                                add_roster_canvas.update()
                                time.sleep(1)  
                            stack['var2'].set(0)

                    roster_results_frame=tk.Frame(add_roster_success_popup)
                    roster_results_frame.pack(side=tk.BOTTOM)
                    results=tk.Label(roster_results_frame,
                                     text=str(successes)
                                     +' successful operation(s)'
                                     +'\n'+str(errors)+' error(s)')
                    results.pack()
                    okay_button=tk.Button(roster_results_frame,text="Okay",
                                          command=lambda:add_roster_success_popup.destroy(),
                                          width=10)
                    okay_button.pack(pady=5)
                    roster_results_frame.update()
                    
                    parent.roster.clear()
                    for child in self.r.winfo_children():
                        child.destroy()
                    self.r.destroy()
                    self.destroy_me=tk.Frame(roster_frame)
                    self.destroy_me.pack(side=tk.TOP, fill=tk.BOTH, anchor=tk.N, expand=True)
                    placeholder_canvas=tk.Canvas(self.destroy_me)
                    placeholder_canvas.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
                    reload()
                except Exception as e:
                    print(e)
            elif add_roster.get()==0 and add_individual.get()==0:
                error=tk.Toplevel()
                error.attributes('-topmost', 1)
                error.wm_title("Error")
                if "nt" == os.name:
                    error.iconbitmap(parent.resource_path('images/icon.ico'))
                error.lift()
                error_label=tk.Label(error, text="No option selected", font=(None, 14))
                error_label.pack(padx=10)
                okay_button=tk.Button(error, text="Okay", command=lambda:error.destroy())
                okay_button.pack(anchor=tk.CENTER, pady=5)
        def openfile():
            try:
                file_loc=filedialog.askopenfilename(title="Select roster",
                                                    filetypes=(("CSV","*.csv"),
                                                                ("All files","*.*")))
                try:
                    roster=read_csv(file_loc, header=None)
                    try:
                        self.destroy_me.destroy()
                        for child in self.r.winfo_children():
                            child.destroy()
                        self.r.destroy()
                        parent.roster.clear()
                    except Exception as e:
                        print(e)
                except Exception as e:
                    print(e)
                
                stud_locate=[]
                nid_locate=[]
                for col in roster.columns:
                    for row in roster[col].items():
                        if "Student".lower() in str(row).lower():
                            nxt_val=roster.iloc[row[0]+1][col]
                            if nxt_val is not ('0' or "nan" or isinstance(nxt_val,str)):
                                stud_locate.append([row[0],col])
                            
                for col in roster.columns:
                    for row in roster[col].items():
                        if "Net ID".lower() in str(row).lower():
                            nxt_val=roster.iloc[row[0]+1][col]
                            if nxt_val is not ('0' or "nan" or not isinstance(nxt_val,str)):
                                nid_locate.append([row[0],col])

                Students=roster[stud_locate[0][1]].tolist()[stud_locate[0][0]+1:]
                ids=roster[nid_locate[0][1]].tolist()[nid_locate[0][0]+1:]

                for i,name in enumerate(Students):
                    new_name=name.split(' ',1)
                    parent.roster.append({'First Name':new_name[1],
                                            'Last Name':new_name[0],
                                            'User Name':ids[i]+'@scarletmail.rutgers.edu'
                                            })

                self.r=tk.Frame(roster_frame)
                self.r.pack(side=tk.TOP, fill=tk.BOTH, anchor=tk.N, expand=True)
                temp_canvas=tk.Canvas(self.r)
                myframe=tk.Frame(temp_canvas)
                
                add_roster_yscrollbar=tk.Scrollbar(self.r, command=temp_canvas.yview)
                add_roster_yscrollbar.pack(side=tk.RIGHT, fill=tk.Y)

                add_roster_xscrollbar=tk.Scrollbar(self.r, orient=tk.HORIZONTAL, command=temp_canvas.xview)
                add_roster_xscrollbar.pack(side=tk.BOTTOM, fill=tk.X)
                
                temp_canvas.config(scrollregion=temp_canvas.bbox(tk.ALL))
                
                temp_canvas.configure(yscrollcommand=add_roster_yscrollbar.set)
                temp_canvas.configure(xscrollcommand=add_roster_xscrollbar.set)
                
                temp_canvas.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
                temp_canvas.create_window((0,0), window=myframe, anchor='nw')

                def onFrameConfigure(event,canvas):
                    canvas.configure(scrollregion=canvas.bbox("all"))

                myframe.bind("<Configure>", lambda event, canvas=temp_canvas: onFrameConfigure(event,canvas))
                self.r.bind("<Enter>", lambda event:_on_mousewheel(event,temp_canvas))
                self.r.bind("<Leave>", lambda event:_off_mousewheel(event,temp_canvas))
                for item in parent.roster:
                    roster_student_canvas=tk.Canvas(myframe, height=11, width=450)
                    roster_student_canvas.pack(fill=tk.X,expand=True)
                    roster_student_canvas.create_text(3,0,text=item['First Name'],anchor=tk.NW, font=(None, 8))
                    roster_student_canvas.create_text(140,0,text=item["Last Name"],anchor=tk.NW, font=(None, 8))
                    roster_student_canvas.create_text(260,0,text=item["User Name"],anchor=tk.NW, font=(None, 8))
                
            except Exception as e:
                print(str(e))      
        
        add_pane=tk.Frame(f2)
        add_pane.pack(fill=tk.BOTH, expand=True)

        add_pane_add_options=tk.Frame(add_pane)
        add_pane_add_options.pack(side=tk.TOP, fill=tk.X)
        
        add_roster_frame=tk.Frame(add_pane_add_options, relief=tk.GROOVE, bd=2)
        add_roster_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        add_roster=tk.IntVar()
        add_individual=tk.IntVar()
        
        add_roster_label=tk.Checkbutton(add_roster_frame,
                                        text="Add roster",
                                        font=(None,14,'bold'),
                                        variable=add_roster,
                                        command=lambda:add_individual.set(0),
                                        takefocus=False)
        add_roster_label.pack(pady=(0,5))
        roster_frame=tk.Frame(add_roster_frame)
        roster_frame.pack(fill=tk.BOTH, expand=True)

        roster_header_canvas=tk.Canvas(roster_frame, height=16)
        roster_header_canvas.pack(fill=tk.X, expand=True, pady=(0,1))
        roster_header_canvas.create_text(3,0,text="First Name",anchor=tk.NW, font=(None, 9, 'bold'))
        roster_header_canvas.create_text(140,0,text="Last Name",anchor=tk.NW, font=(None, 9, 'bold'))
        roster_header_canvas.create_text(260,0,text="User Name",anchor=tk.NW, font=(None, 9, 'bold'))
        roster_header_canvas.create_line(1,16,420,16)

        self.destroy_me=tk.Frame(roster_frame)
        self.destroy_me.pack(side=tk.TOP, fill=tk.BOTH, anchor=tk.N, expand=True)
        placeholder_canvas=tk.Canvas(self.destroy_me)
        placeholder_canvas.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        
        add_roster_browse=tk.Button(add_roster_frame, text="Browse", command=lambda:openfile(), takefocus=False)
        add_roster_browse.pack(fill=tk.X)
        
        add_individual_frame=tk.Frame(add_pane_add_options, relief=tk.GROOVE, bd=2)
        add_individual_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        add_individual_label=tk.Checkbutton(add_individual_frame,
                                            text="Add individual",
                                            font=(None,14,'bold'),
                                            variable=add_individual,
                                            command=lambda:add_roster.set(0),
                                            takefocus=False)
        add_individual_label.pack(pady=(0,10))

        add_label_frame=tk.Frame(add_individual_frame)
        add_label_frame.pack(side=tk.LEFT, anchor=tk.N)

        add_entry_frame=tk.Frame(add_individual_frame)
        add_entry_frame.pack(side=tk.LEFT, anchor=tk.N)
        
        add_individual_FirstName_label=tk.Label(add_label_frame, text="First Name: ")
        add_individual_FirstName_label.pack()
        add_individual_FirstName_entry=tk.Entry(add_entry_frame, width=30)
        add_individual_FirstName_entry.pack()
        
        add_individual_LastName_label=tk.Label(add_label_frame, text="Last Name: ")
        add_individual_LastName_label.pack()
        add_individual_LastName_entry=tk.Entry(add_entry_frame, width=30)
        add_individual_LastName_entry.pack()

        add_individual_UserName_label=tk.Label(add_label_frame, text="Username: ")
        add_individual_UserName_label.pack()
        add_individual_UserName_entry=tk.Entry(add_entry_frame, width=30)
        add_individual_UserName_entry.pack()

        new_user_stack_frame_border=tk.Frame(add_pane, relief=tk.GROOVE, bd=2)
        new_user_stack_frame_border.pack(fill=tk.BOTH, expand=True)

        new_user_stack_frame=tk.Frame(new_user_stack_frame_border)
        new_user_stack_frame.pack(side=tk.TOP, anchor=tk.CENTER)
        new_user_stack_label=tk.Label(new_user_stack_frame,
                                      text="Associate new users with the following stacks:",
                                      font=(None,14,'bold'))
        new_user_stack_label.pack()

        add_button=tk.Button(add_pane, text="Add", font=(None,20), command=lambda: add_user())
        add_button.pack(side=tk.BOTTOM, fill=tk.X)

        #Remove tab
        def BulkRemove():
            if len(remove_bulk_entry.get('1.0',tk.END))>1:
                remove_success_popup=tk.Toplevel()
                remove_success_popup.attributes('-topmost', 1)
                remove_success_popup.wm_title("Results")
                if "nt" == os.name:
                    remove_success_popup.iconbitmap(parent.resource_path('images/icon.ico'))
                remove_success_popup.lift()

                progress_frame=tk.Frame(remove_success_popup)
                progress_frame.pack()
                
                bulk_canvas=tk.Canvas(progress_frame)

                bulk_scrollbar=tk.Scrollbar(progress_frame, command=bulk_canvas.yview)
                bulk_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

                bulkx_scrollbar=tk.Scrollbar(progress_frame, command=bulk_canvas.xview, orient=tk.HORIZONTAL)
                bulkx_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

                bulk_canvas.configure(yscrollcommand=bulk_scrollbar.set)
                bulk_canvas.configure(xscrollcommand=bulkx_scrollbar.set)

                bulk_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

                bulk_frame=tk.Frame(bulk_canvas)
                bulk_canvas_frame=bulk_canvas.create_window((0,0), window=bulk_frame, anchor='nw')
                bulk_frame.bind('<Configure>', lambda event:on_configure(event,bulk_canvas))
                bulk_canvas.bind("<Enter>", lambda event:_on_mousewheel(event,bulk_canvas))
                bulk_canvas.bind("<Leave>", lambda event:_off_mousewheel(event,bulk_canvas))

                errors=0
                successes=0
                
                for user in remove_bulk_entry.get('1.0',tk.END).split('\n')[:-1]:
                    if len(user) != 0:
                        account=tk.Frame(bulk_frame)
                        account.pack(anchor=tk.W)
                        removed=tk.Label(account, text=user+' - ')
                        removed.pack(side=tk.LEFT)
                        try:
                            parent.client.delete_user(UserName=user,AuthenticationType="USERPOOL")
                        except Exception as e:
                            error=tk.Label(account, text=str(e), foreground='red')
                            error.pack(side=tk.LEFT)
                            errors+=1
                        else:
                            removed_account=tk.Label(account, text="Removed successfully", foreground="green")
                            removed_account.pack(anchor=tk.W)
                            successes+=1
                        bulk_canvas.update()
                        bulk_canvas.yview_moveto(1)
                        time.sleep(1)
                results_frame=tk.Frame(remove_success_popup)
                results_frame.pack(side=tk.BOTTOM)
                results=tk.Label(results_frame, text=str(successes)+' account(s) removed successfully.\n'+str(errors)+' error(s).')
                results.pack()
                okay_button=tk.Button(results_frame, text="Okay", command=lambda:remove_success_popup.destroy(),width=10)
                okay_button.pack(pady=5)
                results_frame.update()
                remove_bulk_entry.delete('1.0',tk.END)
                reload()
        def RemoveAll():
            def confirm():
                remove_all_warning.destroy()
                remove_all_nuke=tk.Toplevel()
                remove_all_nuke.attributes('-topmost',1)
                remove_all_nuke.wm_title('Removing...')
                if "nt" == os.name:
                    remove_all_nuke.iconbitmap(parent.resource_path('images/icon.ico'))
                remove_all_nuke.lift()
                remove_all_header=tk.Label(remove_all_nuke, text="Removing...")
                remove_all_header.pack()

                removal_canvas=tk.Canvas(remove_all_nuke)
                removal_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

                removal_scrollbar=tk.Scrollbar(remove_all_nuke, command=removal_canvas.yview)
                removal_scrollbar.pack(side=tk.LEFT, fill=tk.Y)

                removal_canvas.configure(yscrollcommand=removal_scrollbar.set)

                removal_frame=tk.Frame(removal_canvas)
                removal_canvas_frame=removal_canvas.create_window((0,0), window=removal_frame, anchor='nw')
                removal_frame.bind('<Configure>', lambda event:on_configure(event,removal_canvas))
                removal_canvas.bind("<Enter>", lambda event:_on_mousewheel(event,removal_canvas))
                removal_canvas.bind("<Leave>", lambda event:_off_mousewheel(event,removal_canvas))

                errors=0
                successes=0

                for user in parent.user_list:
                    if user['UserName'] not in remove_all_entry.get('1.0',tk.END).split('\n')[:-1]:
                        account=tk.Frame(removal_frame)
                        account.pack(anchor=tk.W)
                        removed=tk.Label(account, text=user['UserName']+' - ')
                        removed.pack(side=tk.LEFT)
                        try:
                            parent.client.delete_user(UserName=user['UserName'],AuthenticationType="USERPOOL")
                        except Exception as e:
                            error=tk.Label(account, text=str(e), foreground='red')
                            error.pack(side=tk.LEFT)
                            errors+=1
                        else:
                            success=tk.Label(account, text="completed", foreground='green')
                            success.pack(side=tk.LEFT)
                            successes+=1
                        removal_canvas.update()
                        removal_canvas.yview_moveto(1)
                        time.sleep(1)
                status_update=tk.Label(remove_all_nuke, text=str(successes)+" removed successfully. "+str(errors)+" error(s)")
                status_update.pack(side=tk.BOTTOM)
                remove_all_close=tk.Button(remove_all_nuke, text="Okay", command=lambda:remove_all_nuke.destroy())
                remove_all_close.pack(side=tk.BOTTOM)
                remove_all_entry.delete('1.0',tk.END)
                reload()
            reload()    
            remove_all_warning=tk.Toplevel()
            remove_all_warning.attributes('-topmost',1)
            remove_all_warning.wm_title("Warning!")
            if "nt" == os.name:
                remove_all_warning.iconbitmap(parent.resource_path('images/icon.ico'))
            remove_all_warning.lift()
            remove_all_warning_header=tk.Label(remove_all_warning, text="Warning", font=(None, 18, 'bold'),
                                               foreground='red')
            remove_all_warning_header.pack(anchor=tk.W)
            if remove_all_entry.compare("end-1c","==","1.0"):
                to_be_removed=0
            else:
                to_be_removed=len(remove_all_entry.get('1.0',tk.END).split('\n')[:-1])
            users_to_be_removed=len(parent.user_list)-to_be_removed
            remove_all_warning_subtext=tk.Label(remove_all_warning,
                                                text=str(users_to_be_removed)+" removal(s) will be attempted",
                                                font=(None, 10, 'italic'))
            remove_all_warning_subtext.pack()
            remove_all_quit_button=tk.Button(remove_all_warning, text="Cancel",
                                             command=lambda:remove_all_warning.destroy())
            remove_all_quit_button.pack(side=tk.LEFT)
            remove_all_confirm_button=tk.Button(remove_all_warning, text="Proceed",
                                                command=lambda:confirm())
            remove_all_confirm_button.pack(side=tk.LEFT)
            
        remove_errors=[]
        remove_success=[]
        remove_pane=tk.Frame(f3)
        remove_pane.pack(fill=tk.BOTH, expand=True)

        remove_bulk_frame=tk.Frame(remove_pane, relief=tk.GROOVE, bd=2)
        remove_bulk_frame.pack(fill=tk.BOTH, expand=True)
        remove_bulk_label=tk.Label(remove_bulk_frame, text="Batch remove", font=(None,14,'bold'))
        remove_bulk_label.pack(side=tk.TOP, anchor=tk.NW)
        remove_bulk_comment=tk.Label(remove_bulk_frame,
                                     text="Enter UserNames of accounts you would like to remove (case-sensitive)\nSeperate entries with a new line",
                                     font=(None,9,'italic'), justify=tk.LEFT)
        remove_bulk_comment.pack(anchor=tk.W,pady=(0,5))
        remove_bulk_content=tk.Frame(remove_bulk_frame)
        remove_bulk_content.pack(side=tk.LEFT, anchor=tk.N, fill=tk.BOTH, expand=True)
        remove_bulk_entry=ScrolledText(remove_bulk_content, width=60, height=10)
        remove_bulk_entry.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        remove_bulk_button=tk.Button(remove_bulk_content, text="Remove",
                                     command=lambda:BulkRemove(),
                                     width=20,
                                     height=3,
                                     font=(None,14))
        remove_bulk_button.pack(side=tk.LEFT, fill=tk.Y)

        remove_all_frame=tk.Frame(remove_pane, relief=tk.GROOVE, bd=2)
        remove_all_frame.pack(fill=tk.BOTH, expand=True)
        remove_all_label=tk.Label(remove_all_frame, text="Remove all", font=(None,14,'bold'))
        remove_all_label.pack(side=tk.TOP, anchor=tk.NW)
        remove_all_comment=tk.Label(remove_all_frame,
                                    text="Enter UserNames of accounts you would like to keep\nSeperate entries with a new line",
                                    font=(None,9,'italic'), justify=tk.LEFT)
        remove_all_comment.pack(anchor=tk.W, pady=(0,5))
        remove_all_content=tk.Frame(remove_all_frame)
        remove_all_content.pack(side=tk.LEFT, anchor=tk.N, fill=tk.BOTH, expand=True)
        remove_all_entry=ScrolledText(remove_all_content, width=60, height=10)
        remove_all_entry.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        remove_all_button=tk.Button(remove_all_content,
                                    text="NUKE",
                                    font=(None,14),
                                    width=20,
                                    height=3,
                                    command=lambda:RemoveAll(),
                                    background="#ffc7c7",
                                    activebackground="#ffa2a2",
                                    foreground="#b00000",
                                    activeforeground="#6e0000"
                                    )
        remove_all_button.pack(side=tk.LEFT, fill=tk.Y)
        
        #wait for login/credentials window to close
        root.wait_window(parent.popup)
        parent.GetUserList()
        parent.GetStacks()
        
        #Post login window creation
        #Manage tab, post-login
        self.canvas=tk.Canvas(user_pane)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.user_canvas_name=self.canvas

        self.scrollbar=tk.Scrollbar(user_pane, command=self.canvas.yview)
        self.scrollbar.pack(side=tk.LEFT, fill='y')
        self.user_scrollbar_name=self.scrollbar 

        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.frame=tk.Frame(self.canvas)
        self.canvas_frame=self.canvas.create_window((0,0), window=self.frame, anchor='nw')
        self.frame.bind('<Configure>', lambda event:on_configure(event,self.canvas))
        self.frame.bind("<Enter>", lambda event:_on_mousewheel(event,self.canvas))
        self.frame.bind("<Leave>", lambda event:_off_mousewheel(event,self.canvas))
        search_button.configure(command=lambda: search(search_field.get(),parent.user_list))
        
        if parent.client:
            stacks_warning.destroy()
            for item in parent.stacks:
                stack=tk.Checkbutton(stacks_frame, text=item['Name'], variable=item['var'])
                stack2=tk.Checkbutton(new_user_stack_frame, text=item['Name'], variable=item['var2'])
                if parent.client.describe_fleets(
                    Names=[parent.client.list_associated_fleets(StackName=item['Name'])['Names'][0]]
                    )['Fleets'][0]['State']=='STOPPED':
                    #Set stack name to red if the associated fleet is stopped
                    #Can stacks have multiple associated fleets?
                    stack.configure(foreground="red",activeforeground="red")
                    stack2.configure(foreground="red",activeforeground="red")
                stack.pack(anchor=tk.NW)
                stack2.pack(side=tk.LEFT)
            for i in parent.user_list:
                canvas2=tk.Canvas(self.frame,width=500, height=17,highlightthickness=0)
                canvas2.pack()
                canvas2.create_text(3,0,text=i['FirstName'],anchor=tk.NW)
                canvas2.create_text(150,0,text=i['LastName'],anchor=tk.NW)
                canvas2.create_text(295,0,text=i['UserName'],anchor=tk.NW)
                canvas2.bind("<1>", lambda event,i=i:click(event,i))
        root.bind('<Return>',lambda event:search(search_field.get(),parent.user_list))

if __name__ == "__main__":
    root=tk.Tk()
    MainApplication(root).pack(side="top", fill=tk.BOTH)
    root.mainloop()

