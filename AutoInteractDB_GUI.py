import logging.config
import logging.handlers
import time
import tkinter as tk  # Python 3.x
from threading import Thread
from tkinter import filedialog as fd
from tkinter import ttk, IntVar
import tkinter.scrolledtext as ScrolledText
from tkinter.messagebox import askyesnocancel
from tkinter.messagebox import showinfo
from tkinter.messagebox import showwarning
import sys
import yaml
import traceback
from Table.recurring_charging import *

class TextHandler(logging.Handler):
    # This class allows you to log to a Tkinter Text or ScrolledText widget
    # Adapted from Moshe Kaplan: https://gist.github.com/moshekaplan/c425f861de7bbf28ef06

    def __init__(self, text):
        # run the regular Handler __init__
        logging.Handler.__init__(self)
        # Store a reference to the Text it will log to
        self.text = text
        self.text.tag_config("info", foreground='blue')
        self.text.tag_config("warning", foreground='orange')
        self.text.tag_config("error", foreground='red')

    # def delete(self):
    #     self.text.delete(1.0, tk.END)

    def emit(self, record):
        msg = self.format(record)

        def append():
            self.text.configure(state='normal')
            lastPos = self.text.index("end-1c")
            self.text.insert(tk.END, msg + '\n')
            self.text.configure(state='disabled')
            self.text.highlight_pattern(r"INFO", "info", start=lastPos, regexp=True)
            self.text.highlight_pattern(r"WARNING", "warning", start=lastPos, regexp=True)
            self.text.highlight_pattern(r"ERROR", "error", start=lastPos, regexp=True)
            # Autoscroll to the bottom
            self.text.yview(tk.END)

        # This is necessary because we can't modify the Text from other threads
        self.text.after(0, append)


class CustomText(tk.scrolledtext.ScrolledText):

    def __init__(self, *args, **kwargs):
        tk.scrolledtext.ScrolledText.__init__(self, *args, **kwargs)

    def highlight_pattern(self, pattern, tag, start="1.0", end="end",
                          regexp=False):

        start = self.index(start)
        end = self.index(end)
        self.mark_set("matchStart", start)
        self.mark_set("matchEnd", start)
        self.mark_set("searchLimit", end)

        count = tk.IntVar()
        while True:
            index = self.search(pattern, "matchEnd", "searchLimit",
                                count=count, regexp=regexp)
            if index == "": break
            if count.get() == 0: break  # degenerate pattern which matches zero-length strings
            self.mark_set("matchStart", index)
            self.mark_set("matchEnd", "%s+%sc" % (index, count.get()))
            self.tag_add(tag, "matchStart", "matchEnd")


class wadGUI(tk.Frame):

    # This class defines the graphical user interface
    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.isShowBrowser = True
        self.root = parent
        self.root.configure(background="black")

        # self.root.geometry("800x400")
        self.root.columnconfigure(0)
        self.root.columnconfigure(1)
        self.root.columnconfigure(2)
        self.root.columnconfigure(3)
        self.root.columnconfigure(4)
        self.root.columnconfigure(5)
        self.root.columnconfigure(6)
        

        with open('conf/logging.yml', 'r') as f:
            try:
                _logconfig = yaml.safe_load(f.read())
                logging.config.dictConfig(_logconfig)
            except yaml.YAMLError as exc:
                print(exc)
                exit(1)
        self.logger = logging.getLogger(self.__class__.__name__)

        #self.logger.info("Initializing GUI")

        self.build_gui()
        self.isStopDeploy = False
        self.isReRun = False
        self.templateFile = ""

        self.logger.info("Initialized GUI")


    def build_gui(self):
        # Build GUI
        self.root.title('vOCS3.0 Auto Interact Database - 1.0.0')
        self.root.option_add('*tearOff', 'FALSE')
        self.root.resizable(False, False)


        self.label = tk.Label(self.root, text='Template:', background="pink")
        self.label.grid(column=0, row=0, sticky=tk.EW, padx=5, pady=5)

        self.temp_dir = tk.StringVar()
        self.tempdir_entry = ttk.Entry(self.root,
                                       textvariable=self.temp_dir)

        self.tempdir_entry.grid(column=1, row=0, sticky=tk.EW, columnspan=3)


        self.button_browser = ttk.Button(self.root, text="...", width=5)
        self.button_browser['command'] = self.select_file
        self.button_browser.grid(column=4, row=0, sticky='w')

        self.button_start = ttk.Button(self.root, text="Start")
        self.button_start['command'] = self.button_callback
        self.button_start.grid(column=5, row=0, sticky=tk.EW)

        self.button_stop = ttk.Button(self.root, text="Stop")
        self.button_stop['command'] = self.button_stop_callback
        self.button_stop.grid(column=6, row=0, sticky=tk.EW)
        self.button_stop["state"] = "disable"

        # self.button_hideshow = ttk.Button(self.root, text="Hide/Show Browser")
        # self.button_hideshow['command'] = self.button_hideshow_callback
        # self.button_hideshow.grid(column=5, row=1, sticky=tk.EW)

        self.button_about = ttk.Button(self.root, text="About")
        self.button_about['command'] = self.button_about_callback
        self.button_about.grid(column=6, row=1, sticky=tk.EW)
        

        self.lblIP = tk.Label(self.root, text='IP:', background="pink")
        self.lblIP.grid(column=0, row=1, sticky=tk.EW, padx=5, pady=5)

        self.IPvar = tk.StringVar()
        self.IP_entry = ttk.Entry(self.root,
                                   textvariable=self.IPvar)
        
        self.IP_entry.grid(column=1, row=1, sticky=tk.EW, columnspan=3)

        self.lblport = tk.Label(self.root, text='Port:', background="pink")
        self.lblport.grid(column=0, row=2, sticky=tk.EW, padx=5, pady=5)

        self.portvar = tk.StringVar()
        self.port_entry = ttk.Entry(self.root,
                                   textvariable=self.portvar)

        self.port_entry.grid(column=1, row=2, sticky=tk.EW, columnspan=3)

        self.lblschema = tk.Label(self.root, text='Schema:', background="pink")
        self.lblschema.grid(column=0, row=3, sticky=tk.EW, padx=5, pady=5)

        self.schemavar = tk.StringVar()
        self.schema_entry = ttk.Entry(self.root,
                                   textvariable=self.schemavar)

        self.schema_entry.grid(column=1, row=3, sticky=tk.EW, columnspan=3)

        self.checkvar = IntVar()
        self.enableLogcheckbox = tk.Checkbutton(self.root, text='Log Enable', onvalue='1', offvalue='0',
                                                variable=self.checkvar)
        self.enableLogcheckbox.grid(column=1, row=4, sticky=tk.EW, padx=5, pady=5)
        self.enableLogcheckbox.select()

        self.labelmodelog = tk.Label(self.root, text='Mode Log:')
        self.labelmodelog.grid(column=2, row=4, sticky=tk.E)

        self.modeLogcbb = ttk.Combobox(self.root)
        self.modeLogcbb.grid(column=3, row=4, sticky=tk.E)
        self.modeLogcbb["state"] = "readonly"
        self.modeLogcbb["value"] = (
            'DEBUG',
            'INFO',
            'WARNING',
            'ERROR'
        )
        self.modeLogcbb.current(0)

        # Add text widget to display logging info
        # self.st = ScrolledText.ScrolledText(self.root, state='normal')

        self.st = CustomText(self.root, state='normal', background="pink")
        self.st.configure(font='TkFixedFont', width=100)
        self.st.grid(column=0, row=5, sticky=tk.EW, columnspan=7)

                # Create textLogger
        self.text_handler = TextHandler(self.st)

        self.button_rerun = ttk.Button(self.root, text="Re-run")
        self.button_rerun['command'] = self.button_rerun_callback
        self.button_rerun["state"] = "disable"
        self.button_rerun.grid(column=5, row=1, sticky=tk.EW)

        if self.checkvar.get() == 1:
            self.text_handler.setLevel(self.modeLogcbb.get())
            self.text_handler.setFormatter(
                logging.Formatter('%(asctime)s [%(name)s] [%(funcName)s] [%(threadName)s] %(levelname)s %(message)s'))
            logging.getLogger().addHandler(self.text_handler)

        with open('conf/systemConfiguration.yml', 'r') as f:
            try:
                config = yaml.safe_load(f.read())
                self.IPvar.set(config["autointeractDB"]["IP"])
                self.portvar.set(config["autointeractDB"]["Port"])
                self.schemavar.set(config["autointeractDB"]["Schema"])
                self.logger.info("Loaded DB connection: " + self.IPvar.get() + ":" + self.portvar.get() + "/" + self.schemavar.get())
            except yaml.YAMLError as exc:
                self.logger.error("Loading connection, yaml file error: " + str(exc))
            except KeyError as exc:
                self.logger.error("Loading connection, KeyError: " + str(exc))
            except:
                self.logger.error("There is some error when loading connection")
                self.logger.error(str(sys.exc_info()))

    def button_callback(self):
        if self.tempdir_entry.get() == "":
            showwarning('Warning', 'The template file directory is empty, please choose one')
            return
        answer = askyesnocancel(title='AutoInteractDB', message='Do you want to execute interacting, with your heart?')
        if answer:
            self.logger.info("Initializing automatically interaction database")
            deploy_thread = Deploy()
            deploy_thread.set_templateFile(self.tempdir_entry.get())
            deploy_thread.set_IP(self.IPvar.get())
            deploy_thread.set_Port(self.portvar.get())
            deploy_thread.set_Schema(self.schemavar.get())
            deploy_thread.start()
            self.monitor(deploy_thread)
            self.button_start["state"] = "disable"
            self.button_stop["state"] = "active"
            self.isStopDeploy = False

    def button_rerun_callback(self):
        self.isReRun = True

    def button_stop_callback(self):
        answer = askyesnocancel(title='AutoInteractDB', message='Do you want to stop deploying, seriously?')
        if answer:
            self.logger.info("You just chose stopping deploy.")
            self.isStopDeploy = True

    def button_about_callback(self):
        showinfo('AutoInteractDB',
                 'The tool supporting to interact automatically with database (version vOCS3.0).\n'
                 'Verion: 1.0.0.\n'
                 'Author: BO OCS.\n'
                 'Coder: Anhnn91\n'
                 'Tester: TuatLV\n'
                 'Version Change:\n'
                 '- 1.0.0: Release first version',
                 )

    def button_clearLog_callback(self):
        self.st.delete(0, tk.END)

    def monitor(self, thread):
        if thread.is_alive():
            # check the thread every 100ms
            self.after(100, lambda: self.monitor(thread))
            if self.isStopDeploy:
                thread.kill()
                self.isStopDeploy = False
                self.logger.info("Thread " + thread.getName() + " is being killed. Waiting until thread is stopped.")
            if self.isReRun:
                self.isReRun = False
                thread.set_state_rerun()
            if thread.get_state() == "Finish" or thread.get_state() == "Error":
                self.button_rerun["state"] = "active"
            else:
                self.button_rerun["state"] = "disable"
        else:
            self.button_start["state"] = "active"
            self.button_stop["state"] = "disable"
            self.button_rerun["state"] = "disable"
            self.logger.info("Thread " + thread.getName() + " is stopped")

    def select_file(self):
        filetypes = (
            ('text files', '*.yml'),
            ('All files', '.')
        )

        filename = fd.askopenfilename(
            title='Open a file',
            initialdir='./',
            filetypes=filetypes)
        self.temp_dir.set(filename)


class Deploy(Thread):
    def __init__(self):
        super().__init__()
        self.templateFile = ""
        self.IP = ""
        self.Port = ""
        self.Schema = ""
        self.state = "Begin"
        self.killed = False
        self.logger = logging.getLogger(self.__class__.__name__)

    def set_templateFile(self, templateFileDir):
        self.templateFile = templateFileDir

    def set_IP(self, IP):
        self.IP = IP
    
    def set_Port(self, Port):
        self.Port = Port
    
    def set_Schema(self, Schema):
        self.Schema = Schema

    def get_state(self):
        return self.state

    def set_state_rerun(self):
        self.state="Rerun"

    def globaltrace(self, frame, event, arg):
        if event == 'call':
            return self.localtrace
        else:
            return None

    def localtrace(self, frame, event, arg):
        if self.killed:
            self.logger.debug("Closed GUI")
            if event == 'line':
                raise SystemExit()
        return self.localtrace

    def kill(self):
        self.killed = True

    def run(self):
        while True:
            self.runc()
            if self.state == "Stop":
                self.logger.debug("runc stopped")
                break
            while self.state != "Rerun":
                if self.state == "Stop":
                    break
                time.sleep(5)
            self.logger.debug("runc will be re-run")

        while True:
            try:
                time.sleep(10)
                if self.state == "Rerun":
                    self.logger.info("Rerun button is clicked, keep brower, title: " + self.root.title)
                    break
            except:
                self.logger.info("Browser quited " + self.root.title)
                self.state = "Stop"
                break
    
    def runc(self):
        sys.settrace(self.globaltrace)
        self.logger.info("AutoInteractDB starts")
        self.logger.info("Loading configuration template from " + self.templateFile + " file")
        with open(self.templateFile, "r") as stream:
            try:
                dictConfig = yaml.safe_load(stream)
                self.logger.debug("Configuration template after loaded:")
                self.logger.debug(str(dictConfig))
            except yaml.YAMLError as exc:
                self.logger.error(exc)
                self.logger.error(traceback.print_exc())
                exit(1)
            except BaseException as exc:
                self.logger.error(exc)
                self.logger.error(str(sys.exc_info()))
                exit(1)
        try:
            for i in range(0, len(dictConfig)):
                self.logger.info("Deploy " + str(dictConfig[i]["AutoInteractDB"]))
                if dictConfig[i].get("AutoInteractDB") is None:
                    self.logger.warning("This interaction is none")
                    continue
                if dictConfig[i]["AutoInteractDB"].get("table") is None:
                    self.logger.warning("The " + "Interaction " + str(i + 1) + " has not table, ignore")
                    continue
                if dictConfig[i]["AutoInteractDB"].get("offer_external_ID") is None:
                    self.logger.warning("The " + "Interaction " + str(i + 1) + " has not offer_external_ID, ignore")
                    continue
                if dictConfig[i]["AutoInteractDB"]["table"] == "Recurring Charging":
                    self.logger.debug("Run to insert into table [" + str(dictConfig[i]["AutoInteractDB"]["table"]) + "]")
                    step = RecurringCharging(dictConfig[i]["AutoInteractDB"])
                    step.run()
                self.logger.info("TEMPLATE HAS BEEN DEPLOYED COMPLETELY!!!")
                self.state = "Finish"
        except KeyError:
            self.logger.error("One of key doesn't exist in dictConfig")
            pass
        except BaseException as ex:
            self.logger.error("Exception occured when deploying: " + str(ex))
            self.logger.error(str(sys.exc_info()))
            self.state = "Error"

if __name__ == "__main__":
    root = tk.Tk()

    wadGUI(root)

    root.mainloop()
