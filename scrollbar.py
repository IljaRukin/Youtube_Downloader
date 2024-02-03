import tkinter as tk

root = tk.Tk()
#root.title("bar")
#root.geometry("600x400")

#canvas & scrollbar - root
canvas = tk.Canvas(root)
scroll = tk.Scrollbar(root, orient="vertical")

#place canvas & scrollbar
scroll.grid(row=0, column=1, sticky="nes") #grid#
#scroll.pack(side="right", fill="y") #pack#
canvas.grid(row=0, column=0, sticky="nsew") #grid#
#canvas.pack(fill="both", expand=1, anchor="nw") #pack#

#enable scrolling
scroll.configure(command=canvas.yview)
canvas.configure(yscrollcommand=scroll.set)
canvas.bind("<Enter>",
		lambda _: canvas.bind_all('<MouseWheel>', 
				lambda e: canvas.config( canvas.yview_scroll(int(-1*(e.delta/120)), "units") )
		)
)

#frame for content - root
frame = tk.Frame(canvas, background="#FFFFFF")
pRow = 0

#label - frame
title1 = tk.Label(frame, text='title')
title1.grid(row=pRow, column=0, sticky="n") #grid#
#title1.pack(anchor="n") #pack#
pRow += 1

#entries - frame
for i in range(20):
    input = tk.Label(frame, text="Text"+str(i+1).zfill(3))
    input.grid(row=pRow, column=0, sticky="") #grid#
    #input.pack(anchor="center") #pack#
    pRow += 1

#button - frame
submitButton = tk.Button(frame, text="done", command=root.destroy)
submitButton.grid(row=pRow, column=0, sticky="s") #grid#
#submitButton.pack(anchor="s") #pack#
pRow += 1

#add frame to canvas - canvas
wrapFrame = canvas.create_window((0,0), window=frame, anchor="nw")

def onFrameConfigure(canvas):
    canvas.configure(scrollregion=canvas.bbox("all")) #show scroll bar
    canvas.itemconfigure(wrapFrame, width=canvas.winfo_width()) #correct canvas size
    return None
canvas.bind("<Configure>", lambda e: onFrameConfigure(canvas))

# expand canvas
root.columnconfigure((0), weight=1) #grid#
root.rowconfigure((0), weight=1) #grid#

# expand frame
frame.columnconfigure((0), weight=1) #grid#
frame.rowconfigure((0), weight=1) #grid#

root.mainloop()