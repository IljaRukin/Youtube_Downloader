import tkinter as tk
import tkinter.ttk as ttk

class Gui(tk.Tk):
		def __init__(self):
				super().__init__()

				log_frame = tk.Frame(self)#, width=300, height=200
				log_frame.pack(side = tk.TOP, padx='5', pady='5')
				log_frame.rowconfigure(0, weight=1)
				log_frame.columnconfigure(0, weight=1)
				
				#log output
				textbox = tk.Text(log_frame, height=6)
				textbox.pack(side = tk.TOP)
				textbox.insert('1.0', "...")
				textbox.config(state='disabled')
				scrollb = tk.Scrollbar(log_frame, command=textbox.yview)
				textbox.config(yscrollcommand=scrollb.set)
				
				comand_frame0 = tk.Frame(self)
				comand_frame0.pack(side = tk.TOP, padx='5', pady='5')

				tk.Label(comand_frame0, text="link extraction ot media download ?").pack(side = tk.TOP)

				#radiobutton video/audio -> filename video/audio
				self.extractOnly = tk.IntVar()
				tk.Radiobutton(comand_frame0,
										text="extract",
										padx = 20,
										variable=self.extractOnly,
										value=True,
										command=self.hideFrame).pack(side = tk.LEFT)
				tk.Radiobutton(comand_frame0,
										text="download",
										padx = 20,
										variable=self.extractOnly,
										value=False,
										command=self.showFrame).pack(side = tk.LEFT)
				self.extractOnly.set(False)
				
				self.comand_frame1 = tk.Frame(self)
				self.comand_frame1.pack(side = tk.TOP, padx='5', pady='5')

				tk.Label(self.comand_frame1, text="for download select media output format:").pack(side = tk.TOP)

				#radiobutton video/audio -> filename video/audio
				self.audioOnly = tk.IntVar()
				tk.Radiobutton(self.comand_frame1,
										text="Audio",
										padx = 20,
										variable=self.audioOnly,
										value=True).pack(side = tk.LEFT)
				tk.Radiobutton(self.comand_frame1,
										text="Video",
										padx = 20,
										variable=self.audioOnly,
										value=False).pack(side = tk.LEFT)
				self.audioOnly.set(True)
				
				
				self.comand_frame2 = tk.Frame(self)
				self.comand_frame2.pack(side = tk.TOP, padx='5', pady='5')

				#link		 -> extract/download
				tk.Button(self.comand_frame2, text='one Link', command=self.doStuff).pack(side = tk.LEFT, padx='5', pady='5')

				#playlist -> extract/download
				tk.Button(self.comand_frame2, text='full Playlist', command=self.doStuff).pack(side = tk.LEFT, padx='5', pady='5')
				
				#channel	-> extract/download
				tk.Button(self.comand_frame2, text='Channel uploads', command=self.doStuff).pack(side = tk.LEFT, padx='5', pady='5')
				
				'''
				if len(text)>0:
						self.textbox.grid(row=0, column=0, sticky='nsew')
						self.scrollb.grid(row=0, column=1, sticky='nsew')
						self.geometry('350x160')
				else:
						self.textbox.grid_forget()
						self.scrollb.grid_forget()
						self.geometry('350x75')
				'''
				
		def hideFrame(self):
				self.comand_frame1.pack_forget()
						
		def showFrame(self):
				self.comand_frame1.pack(side = tk.TOP, padx='5', pady='5',
														before=self.comand_frame2)
						
		@staticmethod
		def doStuff(self):
				print("doing stuff")
				
		@staticmethod
		def doSomething(self):
				print("running")
				title = "my title"
				message = "my message"
				windowPopUp(title, message)

class windowPopUp(tk.Toplevel):
		
		def __init__(self, title, message):
				tk.Toplevel.__init__(self)
				self.title(title)
				self.geometry('350x75')
				self.minsize(350, 75)
				self.maxsize(425, 250)
				self.rowconfigure(0, weight=0)
				self.rowconfigure(1, weight=1)
				self.columnconfigure(0, weight=1)

				button_frame = tk.Frame(self)
				button_frame.grid(row=0, column=0, sticky='nsew')
				button_frame.columnconfigure(0, weight=1)
				button_frame.columnconfigure(1, weight=1)

				ttk.Label(button_frame, text=message).grid(row=0, column=0, columnspan=2, pady=(7, 7))
				ttk.Button(button_frame, text='OK', command=self.destroy).grid(row=1, column=0, sticky='e')
				ttk.Button(button_frame, text='Details', command=self.selectDuplicates).grid(row=1, column=1, sticky='w')
		
		@staticmethod
		def selectDuplicates():
				print("test")
		
if __name__ == '__main__':
		App = Gui().mainloop()