import tkinter as tk
from tkinter import font
import matplotlib.pyplot as pyplot
from matplotlib.figure import Figure
import matplotlib.animation as animation
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from datetime import datetime
import time

import select
import socket

import threading
from queue import Queue

import xlsxwriter

import email, smtplib, ssl
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

#--------------------------------------------------------------------------------------
class param:
    def __init__(self,Setname,Getname,Value):
            self.Setname = Setname
            self.Getname = Getname
            self.Value = Value
            self.Set(-1)

    def Set(self,value):
            self.Value.set(value)

    def SetAndSend(self,NewValue):
            if IsConnected:
                self.Set(NewValue)
                MSGqueue.Push(str(self.Setname)+ ':' +str(self.Value.get()))
            else:
                print('Warning: Disconnected!')
                
#--------------------------------------------------------------------------------------
class Datapoint:
    def __init__(self,n):
            self.Input = param('T','t',tk.StringVar())
            self.Output = param('O','o',tk.StringVar())
            self.Time = param ('N','n',tk.StringVar())
            self.Input.Set(n)
            self.Output.Set(n)
            self.Time.Set(n)

    def Check(self):
            if (float(self.Input.Value.get()) >-1 and float(self.Output.Value.get()) >-1 and float(self.Time.Value.get()) >-1):
                print("data ready: " + self.Input.Value.get()+' '+self.Output.Value.get()+' '+self.Time.Value.get())
                return True
            else:
                return False
            
#--------------------------------------------------------------------------------------                
class myQueue:
    def __init__(self,name,n):
        self.name = name
        self.queue = Queue(maxsize = n)

    def Pull(self,buf):
        success = False
        if not self.queue.empty():
            buf = self.queue.get()
            self.queue.task_done()
            success = True
        return buf,success
    
    def Clear(self):
        print ("clearing queue: " + self.name)           
        while not self.queue.empty():
            try:
                self.queue.get(False)
                self.queue.task_done()
            except Empty:
                continue

    def Push(self,value):
        if self.queue.full():
            self.queue.get()
            self.queue.task_done()
        self.queue.put(value)
 
#--------------------------------------------------------------------------------------            
class myXlsx:
        def __init__(self):
            date = datetime.now()
            date = date.strftime("%Y%m%d _%H%M")
            self.filename = 'NodeMCU ' + str(date) + '.xlsx'

            self.workbook = xlsxwriter.Workbook(self.filename)
            self.worksheet = self.workbook.add_worksheet()
            self.row = 1
            self.col =0

            self.worksheet.write(0, self.col,     "NodeMCU")
            self.worksheet.write(0, self.col+1,     date)
            self.Write('Mode','Setpoint','P','I','D','Runtime [s]','Input [u]','Output [u]')

        def Write(self,M,S,P,I,D,t,i,o):
            self.worksheet.write(self.row, self.col,     M)
            self.worksheet.write(self.row, self.col+1,     S)
            self.worksheet.write(self.row, self.col+2,     P)
            self.worksheet.write(self.row, self.col+3,     I)
            self.worksheet.write(self.row, self.col+4,     D)
            self.worksheet.write(self.row, self.col+5,     t)
            self.worksheet.write(self.row, self.col + 6,    i)
            self.worksheet.write(self.row, self.col + 7,    o)
            self.row +=1

        def close(self):
            self.workbook.close()

#--------------------------------------------------------------------------------------    
class myMail:
        def __init__(self,sendermail,password):
            date = datetime.now()
            date = date.strftime("%Y-%m-%d")

            subject = "Data from controling session: " + str(date)
            body = "Data from your controler is ready. Please in see attachment"
            self.sender_email = sendermail
            self.password = password

            # Create a multipart message and set headers
            self.message = MIMEMultipart()
            self.message["From"] = self.sender_email
            self.message["Subject"] = subject

            # Add body to email
            self.message.attach(MIMEText(body, "plain"))

        def AddAttachment(self,filename):
            with open(filename, "rb") as attachment:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(attachment.read())
   
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                f"attachment; filename= {filename}",)

            self.message.attach(part)

        def Send(self,recmail):
            self.message["To"] = recmail
            text = self.message.as_string()
            # Log in to server using secure context and send email
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
                server.login(self.sender_email, self.password)
                server.sendmail(self.sender_email, recmail, text)
                                 
#-------------------------------------------------------------------------------------- 
class mygraph:
    def __init__ (self,n,master):
        self.InputList = [0 for x in range(n)]
        self.OutputList = [0 for x in range(n)]
        self.TimeList = [0 for x in range(n)]

        self.graph = Figure(figsize=(5, 3.5), dpi=100)
        grid = pyplot.GridSpec(5, 1)
        self.InputPlot= self.graph.add_subplot(grid[:3, 0])
        self.OutputPlot= self.graph.add_subplot(grid[3:, 0])
        self.graph.set_tight_layout(True)
        
        self.InputPlot.axes.set_ylim(0,1000)
        self.InputPlot.axes.set_yticks([0,100,200,300,400,500,600,700,800,900,1000])
        self.OutputPlot.axes.set_ylim(0,100)
        self.OutputPlot.axes.set_yticks([0,10,20,30,40,50,60,70,80,90,100])

        self.canvas = FigureCanvasTkAgg(self.graph, master)
        self.canvas.draw()
        self.canvas.get_tk_widget().grid(row =2, column= 4, columnspan = 30, rowspan= 24)

    def Animate(self,Dp,Dataready):
        if Dataready:
            self.InputList.append(float(Dp.Input.Value.get()))
            self.InputList.pop(0)
                        
            self.TimeList.append(float(Dp.Time.Value.get()))
            self.TimeList.pop(0)
                        
            self.OutputList.append(float(Dp.Output.Value.get()))
            self.OutputList.pop(0)
        
        self.InputPlot.clear()
        self.OutputPlot.clear()

        self.InputPlot.plot(self.TimeList,self.InputList,'b-')
        self.OutputPlot.plot(self.TimeList,self.OutputList,'r-')

    def Clear(self):
        self.InputPlot.clear()
        self.OutputPlot.clear()
        
#--------------------------------------------------------------------------------------
class Application(tk.Frame):
    
    def __init__ (self, master = None):
            self.Mode = param('M','m',tk.IntVar())
            self.Setpoint = param('S','s',tk.StringVar())
            self.P = param('P','p',tk.StringVar())
            self.I = param('I','i',tk.StringVar())
            self.D = param('D','d',tk.StringVar())

            self.Dp = Datapoint(-1)

            tk.Frame.__init__(self, master)
            self.master = master
            self.master.title("controler")
            self.pack(fill='both', expand=1)
            
            self.create_Buttons()
            self.create_RadioButtons()
            self.create_Entries()
            self.create_Labels()
            self.create_dividers()

            self.graph = mygraph(10,self)
            self.workbook = myXlsx()
            self.requested = False

    def create_Buttons(self):
            self.CloseButton    = tk.Button(self, text ="Exit", command = self.Close, height = 1, width = 7, background= 'White')            
            self.CDButton       = tk.Button(self, text = "Connect", command = self.CD, height = 1, width = 7, background = 'White')            
            self.SetButton       = tk.Button(self, text = "Set All", command = self.SetAll, height = 1, width = 7, background = 'White')            
            self.GetButton       = tk.Button(self, text = "Get All", command = self.GetAll, height = 1, width = 7, background = 'White')            
            self.SendButton     = tk.Button(self, text = "Send", command = self.SendMSG, height = 1, width = 7, background = 'White')

            self.GetButton.grid (row= 16, column = 0)
            self.SetButton.grid (row= 16, column = 2)
            self.CDButton.grid (row =3, column =0)
            self.CloseButton.grid (row= 3, column= 2)
            self.SendButton.grid (row = 18, column = 2)

            self.SetOutputButton = tk.Button(self, text = "Set", command = lambda: self.Dp.Output.SetAndSend(self.OutputEntry.get()), height = 1, width = 5, background = 'White')
            self.SetSetpointButton = tk.Button(self, text = "Set", command = lambda: self.Setpoint.SetAndSend(self.SetpointEntry.get()), height = 1, width = 5, background = 'White')
            self.SetPButton = tk.Button(self, text = "Set", command = lambda: self.P.SetAndSend(self.PEntry.get()), height = 1, width = 5, background = 'White')
            self.SetIButton = tk.Button(self, text = "Set", command = lambda: self.I.SetAndSend(self.IEntry.get()), height = 1, width = 5, background = 'White')
            self.SetDButton = tk.Button(self, text = "Set", command = lambda: self.D.SetAndSend(self.DEntry.get()), height = 1, width = 5, background = 'White')
           
            self.SetOutputButton.grid(row=8, column = 2)
            self.SetSetpointButton.grid(row=11, column = 2)
            self.SetPButton.grid(row=13, column = 2)
            self.SetIButton.grid(row=14, column = 2)
            self.SetDButton.grid (row = 15, column = 2)
                
    def create_RadioButtons(self):
            self.mode = tk.IntVar()
            self.mode.set(0)

            self.OffRadio = tk.Radiobutton(self, text="Off", variable=self.mode, value=0, command= lambda: self.Mode.SetAndSend(0))           
            self.ManualRadio = tk.Radiobutton(self, text="Manual", variable= self.mode, value=1, command= lambda: self.Mode.SetAndSend(1))        
            self.AutoRadio = tk.Radiobutton(self, text="Auto", variable=self.mode, value=2, command= lambda: self.Mode.SetAndSend(2))
            
            self.ManualRadio.grid (row =5, column =1)
            self.OffRadio.grid (row =5, column =0)
            self.AutoRadio.grid (row =5, column =2)
        
    def create_Labels(self):
            self.IntputlabelVar = tk.StringVar()
            self.OutputlabelVar = tk.StringVar()
        
            unifont = font.Font(family= "Times New Roman" , size= 12)

            self.IPLabel= tk.Label (self, text="IP:", font=unifont)
            self.PortLabel= tk.Label (self, text="Port:", font=unifont)

            self.OutputLabel = tk.Label(self, text='Output', font=unifont)
            self.SetpointLabel = tk.Label (self, text ="Setpoint", font=unifont)
            self.PLabel = tk.Label (self, text ="P", font=unifont)
            self.ILabel = tk.Label (self, text ="I", font=unifont)
            self.DLabel = tk.Label (self, text ="D", font=unifont)

            self.IPLabel.grid (row =1, column =0)
            self.PortLabel.grid (row =2, column =0)

            self.OutputLabel.grid(row=8, column =0)
            self.SetpointLabel.grid(row=11, column = 0)
            self.PLabel.grid(row=13, column = 0)
            self.ILabel.grid(row=14, column = 0)
            self.DLabel.grid(row = 15, column = 0)

            self.InputLabel1= tk.Label (self, text="Input:", font=unifont)
            self.InputLabel2=tk.Label (self, textvariable= self.IntputlabelVar, font=unifont)
            self.InputLabel3= tk.Label (self, text="Unit", font=unifont)

            self.InputLabel1.grid(row =1, column =4)
            self.InputLabel2.grid(row =1, column =5)
            self.InputLabel3.grid(row =1, column =6)
          
            self.OutputLabel1= tk.Label (self, text="Output:", font=unifont)
            self.OutputLabel2=tk.Label (self, textvariable= self.OutputlabelVar, font=unifont)
            self.OutputLabel3= tk.Label (self, text="%", font=unifont)
            
            self.OutputLabel1.grid(row =1, column =7)
            self.OutputLabel2.grid(row =1, column =8)
            self.OutputLabel3.grid(row =1, column =9)
        
    def create_Entries(self):
            IP = "192.168.0.228"
            Port = "80"
            
            self.IPEntry = tk.Entry(self, textvariable = IP, width = 20)
            self.PortEntry = tk.Entry(self, textvariable = Port, width = 20)
            
            self.IPEntry.grid (row = 1, column = 1, columnspan = 2, sticky ='E')
            self.PortEntry.grid (row = 2, column = 1, columnspan = 2, sticky ='E')
            
            self.IPEntry.insert ('end', IP)
            self.PortEntry.insert ('end', Port)
            
            self.OutputEntry=tk.Entry(self, width = 10)            
            self.SetpointEntry=tk.Entry(self, width = 10)            
            self.PEntry=tk.Entry(self, width = 10)            
            self.IEntry=tk.Entry(self, width = 10)
            self.DEntry=tk.Entry(self, width = 10)
            
            self.MessageEntry = tk.Entry(self, width = 20)
            
            self.OutputEntry.grid(row=8, column = 1)
            self.SetpointEntry.grid(row=11, column = 1)
            self.PEntry.grid(row=13, column = 1)
            self.IEntry.grid(row=14, column = 1)
            self.DEntry.grid (row = 15, column = 1)
            self.MessageEntry.grid (row = 18, column = 0, columnspan = 2)
            
    def create_dividers(self):
            self.canv = tk.Canvas(self, height = 20, width = 740)
            self.canv.create_line(15,10,725,10, fill = 'black')
            self.canv.grid (row=0, column =0, columnspan=34)
            self.grid_rowconfigure(0,minsize=10)

            self.canv1 = tk.Canvas(self, height = 5, width =200)
            self.canv1.create_line(0,5,200,5, fill = 'black')
            self.canv1.grid(row =6, column =0, columnspan =3)
            self.grid_rowconfigure(6,minsize=5)

            self.canv2 = tk.Canvas(self, height = 5, width = 200)
            self.canv2.create_line(0,5,200,5, fill = 'black')
            self.canv2.grid(row = 17, column = 0, columnspan = 3)
            self.grid_rowconfigure(17,minsize=5)
        
            self.canv3 = tk.Canvas(self, height = 5, width = 200)
            self.canv3.create_line(0,5,200,5, fill = 'black')
            self.canv3.grid(row=9, column =0, columnspan =3)
            self.grid_rowconfigure(9,minsize=5)

            self.canv4 = tk.Canvas(self, height = 380, width = 20)
            self.canv4.create_line(10,0,10,380, fill = 'black')
            self.canv4.grid (row=1, column = 3, rowspan = 25)

    def UpdateEntry(self, Entry, value):
            Entry.delete(0,'end')
            Entry.insert (0, value)
            
    def CD(self):
            self.graph.Clear()
            if IsConnected:
                self.Disconnect()
            else:
                self.Connect()
            
    def Connect(self):
            global s
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            s.settimeout(10.0)
            
            TCPIP = self.IPEntry.get()
            TCPPort = int(self.PortEntry.get())
            print("Connecting to:" + self.IPEntry.get() +"/" + self.PortEntry.get())
            try:
                s.connect((TCPIP,TCPPort))
            except:
                print ("Cannot connect to server")
            else:
                self.CDButton.configure(text="Disconnect")
                global IsConnected
                IsConnected = True
                self.GetAll()
            
    def Disconnect(self):
            global IsConnected
            IsConnected = False
            global s
            try:
                s.close()
            except:
                print ("Cannot disconnect")
                IsConnected = True
            else:
                self.CDButton.configure(text="Connect")
            
    def SendMSG(self):
            if IsConnected:
                try:
                    float(self.MessageEntry.get()[2:])
                except:
                    print("invalid value")
                    return
                MSGqueue.Push(self.MessageEntry.get())
                self.MessageEntry.delete(0,'end')
            else:
                print('Warning: Disconnected!')
           
    def SetAll(self):
            if IsConnected:
                self.Setpoint.SetAndSend(self.SetpointEntry.get())
                self.P.SetAndSend(self.PEntry.get())
                self.I.SetAndSend(self.IEntry.get())
                self.D.SetAndSend(self.DEntry.get())
            else:
                print('Warning: Disconnected!')
            
    def GetAll(self):
            if IsConnected:
                print("Getting current values")
                MSGqueue.Push(self.Mode.Getname+':')
                MSGqueue.Push(self.Dp.Time.Getname+':')
                MSGqueue.Push(self.Dp.Input.Getname+':')
                MSGqueue.Push(self.Dp.Output.Getname+':')
                MSGqueue.Push(self.Setpoint.Getname+':')
                MSGqueue.Push(self.P.Getname+':')
                MSGqueue.Push(self.I.Getname+':')
                MSGqueue.Push(self.D.Getname+':')
                self.requested = True
            else:
                print('Warning: Disconnected!')
        
    def Update(self,i):
            buf = ''
            Dataready = False
            
            if IsConnected:
                    
                buf, success = Modequeue.Pull(buf)
                if success:
                    self.Mode.Set(buf)
                    self.mode.set(self.Mode.Value.get())

                buf, success = Setpointqueue.Pull(buf)
                if success:
                    self.Setpoint.Set(buf)
                    self.UpdateEntry(self.SetpointEntry,self.Setpoint.Value.get())

                buf, success = Pqueue.Pull(buf)
                if success:
                    self.P.Set(buf)
                    self.UpdateEntry(self.PEntry,self.P.Value.get())

                buf, success = Iqueue.Pull(buf)
                if success:
                    self.I.Set(buf)
                    self.UpdateEntry(self.IEntry,self.I.Value.get())

                buf, success = Dqueue.Pull(buf)
                if success:
                    self.D.Set(buf)
                    self.UpdateEntry(self.DEntry,self.D.Value.get())
                    
                self.Dp,Dataready = Dataqueue.Pull(self.Dp)
                self.graph.Animate(self.Dp,Dataready)
                
                self.IntputlabelVar.set(self.Dp.Input.Value.get())
                self.OutputlabelVar.set(self.Dp.Output.Value.get())
                
                if Dataready:
                    self.workbook.Write(self.Mode.Value.get(),\
                                                    float(self.Setpoint.Value.get()),\
                                                    float(self.P.Value.get()),\
                                                    float(self.I.Value.get()),\
                                                    float(self.D.Value.get()),\
                                                    float(self.Dp.Time.Value.get()),\
                                                    float(self.Dp.Input.Value.get()),\
                                                    float(self.Dp.Output.Value.get()))
                    if self.requested:
                            self.UpdateEntry(self.OutputEntry,self.Dp.Output.Value.get())
                            self.requested = False
                                 
    def Close(self):
            if IsConnected:
                self.Disconnect()
            self.workbook.close()

            global Exit
            Exit = True
            
            Modequeue.Clear()
            Dataqueue.Clear()
            Setpointqueue.Clear()
            Pqueue.Clear()
            Iqueue.Clear()
            Dqueue.Clear()
            MSGqueue.Clear()

            EmailThread = threading.Thread(target = RunEmailer, args = [self.workbook.filename])
            EmailThread.start()

            self.master.destroy()
                                 
#--------------------------------------------------------------------------------------
class Messenger:
    def __init__(self):
        self.Dp = Datapoint(-1)
        self.switcher = {
            'M'         : lambda : Modequeue.Push(self.value),
            'P'          : lambda : Pqueue.Push(self.value),
            'I'           : lambda : Iqueue.Push(self.value),
            'D'          : lambda : Dqueue.Push(self.value),
            'S'          : lambda : Setpointqueue.Push(self.value),
            
            'T'           : lambda : self.Dp.Input.Set(self.value),
            'N'          : lambda : self.Dp.Time.Set(self.value),
            'O'          : lambda : self.Dp.Output.Set(self.value)}
            
    def SendMessage(self,message):
        time.sleep(0.05)
        message += '\n'
        global s
        s.sendall(message.encode('utf-8'))

    def GetMessage(self):
        char = b''
        buf = b''
        global s
        while 1:
            try:
                char = s.recv(1)
                
                if '\r' == char.decode('utf-8'):
                    char = s.recv(1)
                    self.SplitMessage(str(buf.decode('utf-8')))
                    return
                else:
                    buf += char
            except:
                print("socket read error")
                return

    def SplitMessage(self,message):
        self.operand = message[0]
        self.value = message[2:]
        self.HandleMessage()

    def HandleMessage(self):
        func = self.switcher.get(self.operand,    lambda: print("Unknown Operand"))
        func()

    def Run(self):
        global s
        global Exit
        self.operand = ''
        self.value = ''
        
        while not Exit:
            time.sleep(0.05)
            if IsConnected:

                buf = ''
                success = False

                buf, success = MSGqueue.Pull(buf)
                while success:
                    self.SendMessage(buf)
                    buf, success = MSGqueue.Pull(buf)
                    
                ready = select.select([s],[],[],2)
                if ready[0]:
                    self.GetMessage()

                if self.Dp.Check():
                    Dataqueue.Push(self.Dp)
                    self.Dp = Datapoint(-1)
                    
#Main----------------------------------------------------------------------------------

def Runmessenger():
    print ("Starting messenger")
    myMessenger = Messenger()
    myMessenger.Run()
    print ("Exiting messenger")

def RunEmailer(filename):
    print ("Starting Emailer")
    Mail = myMail("*sender_mail*","*sender_password")
    Mail.AddAttachment(filename)
    Mail.Send("*reciever_mail*")
    print("Email Sent")

global s 

IsConnected = False
Exit = False

Modequeue = myQueue("Mode", 1)
Dataqueue = myQueue('Data',0)
Setpointqueue = myQueue("Setpoint", 1)
Pqueue = myQueue("P", 1)
Iqueue = myQueue("I", 1)
Dqueue = myQueue("D", 1)
MSGqueue = myQueue("MSG",0)           

root = tk.Tk()
root.geometry("750x420")

app = Application(root)

MessengerThread = threading.Thread(target = Runmessenger)
MessengerThread.start()

ani = animation.FuncAnimation(app.graph, app.Update, interval=500)

app.mainloop()
time.sleep(5)
print ("Shutting down")


