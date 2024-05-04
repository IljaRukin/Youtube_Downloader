import sys
import os
import requests
import pytube
from moviepy.editor import AudioFileClip
from pathvalidate import sanitize_filename
import tkinter as tk
import tkinter.filedialog
import tkinter.ttk as ttk
import traceback
import threading

class DownloadHandler():
	toDownloadLinksFolder = 'toDownloadLinks'
	downloadedLinksFolder = 'downloadedLinks'
	downloadedFilesFolder = 'downloadedFiles'
	messageBuffer = list()
	#self.textbox.insert(tk.END, traceback.format_exc())

	def __init__(self) -> None:
		pass

	def filterId(self, link):
		'''extract video id from url'''
		link = link.strip('\n')
		pos = link.find("?v=")
		return link[pos+3:pos+13+1]

	def filterName(self, filename):
		'''make filename valid for windows'''
		filename = filename.replace('\n','')
		filename = sanitize_filename(filename)
#		filename = filename.lower()
		return filename

	def saveLinks(self, links, path, sourceUrl, names=None):
		'''save links to file in toDownloadLinksFolder'''
		if names==None or len(links)!=len(names):
			names = list()
			for link in links:
				try:
					vid = pytube.YouTube("http://youtube.com/watch?v="+link)
					name = self.filterName( vid.title )
					names.append(name)
				except:
					names.append('-')
		
		try:
			#read contents of already present file
			with open(path,'r',encoding='utf-8') as f:
				#read playlist url from first line
				url = f.readline().strip('\n')
				if url[0]!="#":
					commentStart = url.find("#")
					if commentStart>=0:
						names.append(url[commentStart+1:])
						links.append(url[commentStart:])
					else:
						names.append("-")
						links.append(url)
				else:
					if url[1:]!="-":
						sourceUrl = url[1:]
				
				#read link from file untill start of comment "#" -> add to link
				#read comment -> add to names
				for line in f:
					line = line.strip("\n")
					commentStart = line.find("#")
					if commentStart>0:
						names.append(line[commentStart+1:])
						links.append(line[commentStart:])
					else:
						names.append("-")
						links.append(line)
		except:
			#file does not exist - so create it
			self.messageBuffer.append("creating file "+str(path))
		
		#write all links & comments to file
		with open(path,"w",encoding='utf-8') as f:
			f.write('#%s\n' % sourceUrl)
			while links:
				link = links.pop()
				name = names.pop()
				f.write('%s #%s\n' % (link,name))
		return None

	def loadLinks(self, path):
		"""list links from path"""
		links = list()
		names = list()
		try:
			with open(path,"r",encoding='utf-8') as f:
				#read playlist url from first line
				url = f.readline().strip('\n')
				if url[0]!="#":
					commentStart = url.find("#")
					if commentStart>=0:
						names.append(url[commentStart+1:])
						links.append(url[commentStart:])
					else:
						names.append("-")
						links.append(url)
				else:
					if url[1:]!="-":
						sourceUrl = url[1:]
				
				#read link from file untill start of comment "#" -> add to link
				#read comment -> add to names
				for line in f:
					line = line.strip("\n")
					commentStart = line.find("#")
					if commentStart>0:
						names.append(line[commentStart+1:])
						links.append(line[commentStart:])
					else:
						names.append("-")
						links.append(line)
		except:
			#file does not exist - so create it
			self.messageBuffer.append("creating file "+str(path))
		return links,names

	def listFiles(self, folder, fileEnding=None):
		"""list all files saved in folder\n
		(optionally with specific ending)"""
		fileList = list()
		for (dirpath, dirnames, filenames) in os.walk(folder):
			fileList.extend([os.path.join(dirpath,filename) for filename in filenames])
		
		if fileEnding==None:
			return fileList
		else:
			files = list()
			for file in fileList:
				for ending in fileEnding:
					if file[len(file)-len(ending):]==ending:
						files.append(file)
						break
			return files

	def listOfAllLinks(self, folder, fileEnding=None):
		"""list all links saved in folder in Dict"""
		links = list()
		for file in self.listFiles(folder, fileEnding):
			if os.path.basename(file)=="blackList.txt":
				continue#skip
			[links[file],_] = self.loadLinks(file)
		return links
	
	def dictOfAllLinks(self, folder, fileEnding=None):
		"""list all links saved in folder/files in List"""
		links = dict()
		for file in self.listFiles(folder, fileEnding):
			if os.path.basename(file)=="blackList.txt":
				continue#skip
			[links[file],_] = self.loadLinks(file)
		return links

	def collectLinks(self, playlistUrl):
		"""get all links from playlist"""
		playlist = pytube.Playlist(playlistUrl)
		links = playlist.video_urls
		links = [self.filterId(link) for link in links]
		playlistName = playlist.title
		channelName = playlist.owner
		return links, playlistName, channelName

	def channelPlaylist(self, channelUrl):
		
		#request channel page
		response = requests.get(channelUrl)
		if response.status_code != 200:
			self.messageBuffer.append("failed to load channel url to extract playlist")
		#response.raise_for_status()
		body = response.text
		
		#extract playlist id
		keyword = "\"browseId\":\"UC"
		pos1 = body.find(keyword)+len(keyword)
		pos2 = body.find("\"",pos1)
		playlistUrl = "https://www.youtube.com/playlist?list=UU"
		playlistUrl += body[pos1:pos2]
		
		#extract channel name
		keyword = "\"name\": \""
		pos1 = body.find(keyword)+len(keyword)
		pos2 = body.find("\"",pos1)
		channelName = body[pos1:pos2]
		
		return playlistUrl, channelName
	
	#--- save execution
	
	def findDuplicateLinks(self, newLinksFile):
		"""compare links from newLinksFile to links in files inside downloadedLinksFolder"""
		newLinksPath = os.path.join(self.toDownloadLinksFolder,newLinksFile)
		oldLinks = self.dictOfAllLinks(self.downloadedLinksFolder,[".txt"])
		checkedLinks = list()
		duplicates = dict()
		
		#read all links
		[newLinksList,newNamesList] = self.loadLinks(newLinksPath)
		newLinksList = list(set(newLinksList))
		
		#check all files on duplicates
		while newLinksList:
			newLink = newLinksList.pop()
			linkIsOld = False
			for oldLinksPath,oldLinksList in oldLinks.items():
				if newLink in oldLinksList:
					linkIsOld = True
					if newLink not in duplicates:
						duplicates[newLink] = [newLinksPath]
					duplicates[newLink].append(oldLinksPath)
			if not linkIsOld:
				checkedLinks.append(newLink)
		del newLinksList

		#list all filePaths with duplicates
		allDuplicateFiles = set()
		for link,filePaths in duplicates.items():
			for filePath in filePaths:
				allDuplicateFiles.add(filePath)
		allDuplicateFiles = list(allDuplicateFiles)
		if newLinksPath in allDuplicateFiles:
			allDuplicateFiles.remove(newLinksPath)
		
		return duplicates,checkedLinks,allDuplicateFiles
		
	def deleteDuplicateLinks(self,newLinksFile,checkedLinks,allDuplicateFiles,keepLink,deleteLink):
		newLinksPath = os.path.join(self.toDownloadLinksFolder,newLinksFile)
		
		#edit files
		try:
			#add links to current file
			failed = list()
			try:
				with open(newLinksPath,'w',encoding='utf-8') as f:
					while checkedLinks:
						link = checkedLinks.pop()
						f.write('%s\n' % link)
			except Exception as ex:
				self.messageBuffer.append('error opening file')
				self.messageBuffer.append(str(ex))
				failed.append([link]+checkedLinks)
				raise
			del checkedLinks

			try:
				with open(newLinksPath,'a',encoding='utf-8') as f:
					for link,filePath in keepLink.copy().items():
						if filePath == newLinksPath:
							f.write('%s\n' % link)
							del keepLink[link]
			except Exception as ex:
				self.messageBuffer.append('error on: '+str(link))
				self.messageBuffer.append(str(ex))
				failed.append(list(keepLink.values()))
				raise
			
			#keepLink
				
			#remove links from all other files
			for duplicateFile in allDuplicateFiles: #choose one file
				self.messageBuffer.append(str(duplicateFile))
				toRemove = list()
				for link,filePaths in deleteLink.items(): #loop over all links
					self.messageBuffer.append(str(link))
					if duplicateFile in filePaths: #check if link is in choosen file
						toRemove.append(link)
				if toRemove:
					linkList = list() #read all links from file skippin links in roRemove
					with open(duplicateFile,'r',encoding='utf-8') as f: #read all links except toRemove
						for link in f:
							link = link.strip("\n")
							if link not in toRemove:
								linkList.append(link)
					for link,filePath in keepLink.copy().items(): #add keepLink links if not present already
						if filePath == duplicateFile:
							if link not in linkList:
								linkList.append(link)
							del keepLink[link]
					with open(duplicateFile+".temp",'w',encoding='utf-8') as f: #save links to temp
						for link in linkList:
							f.write('%s\n' % link)
					#if successful: replace duplicateFile with duplicateFile+".temp"
					os.replace(duplicateFile+".temp",duplicateFile)
		except:
			self.messageBuffer.append('Interrupted')
			with open(newLinksPath,'w',encoding='utf-8') as ff:
				for item in failed:
					item = item.strip('\n')
					ff.write('%s\n' % item)
			sys.exit(0)

		return None
	
	### download loop
	def downloadFiles(self, newLinksFile, downloadOnlyAudio=True, authenticate=False):
		[downloadedLinks,downloadedNames] = self.loadLinks(os.path.join(self.downloadedLinksFolder,newLinksFile))
		[blackList,_] = self.loadLinks('toDownloadLinks/blackList.txt')
		failedLinks = list()
		failedNames = list()
		try:
			with open(os.path.join(self.toDownloadLinksFolder,newLinksFile),'r',encoding='utf-8') as f:
				#read playlist url from first line
				firstLine = f.readline().strip('\n')
				lines = f.readlines()
				
				#read playlist url from first line
				sourceUrl = "-"
				if firstLine[0]!="#":
					lines.append(firstLine)
				else:
					if firstLine[1:]!="-":
						sourceUrl = firstLine[1:]
				
				if not os.path.exists( os.path.join(self.downloadedLinksFolder,newLinksFile) ):
					with open(os.path.join(self.downloadedLinksFolder,newLinksFile),'w',encoding='utf-8') as ff:
						ff.write('#%s\n' % sourceUrl)
				
				with open(os.path.join(self.downloadedLinksFolder,newLinksFile),'a',encoding='utf-8') as ff:
					
					numElements = len(lines)
					for iter in range(numElements):
						self.messageBuffer.append('-----'+str(iter+1)+'/'+str(numElements)+'-----')
						line = lines.pop()
						line = line.strip('\n')
						
						#remove name from comment
						commentStart = line.find("#")
						if commentStart>0:
							name = line[commentStart+1:]
							link = line[:commentStart-1]
						else:
							name = "-"
							link = line
						
						if line in blackList:
							failedLinks.append(link)
							failedNames.append(name)
							continue#skip
						if line in downloadedLinks:
							continue#skip
						try:
							self.messageBuffer.append('downloading: '+str(line))
							if authenticate:
								vid = pytube.YouTube("http://youtube.com/watch?v="+link,
														 use_oauth=True, allow_oauth_cache=True)
							else:
								vid = pytube.YouTube("http://youtube.com/watch?v="+link)
							if downloadOnlyAudio:
								#stream = vid.streams.filter(only_audio=True).order_by('resolution').desc().first()
								stream = vid.streams.filter(only_audio=True).get_audio_only()
							else:
								#stream = vid.streams.filter(progressive=True).order_by('abr').desc().first()
								stream = vid.streams.filter(progressive=True).get_highest_resolution()
								#for highest video quality download video and audio separate [.filterName(adaptive=True)] and recombine (e.g. with ffmpeg)
								'''
								import ffmpeg
								input_video = ffmpeg.input('./test/test_video.webm')
								input_audio = ffmpeg.input('./test/test_audio.webm')
								ffmpeg.concat(input_video, input_audio, v=1, a=1).output('./processed_folder/finished_video.mp4').run()
								'''
							#download
							playlistName = newLinksFile[:-4]
							filename = "["+self.filterName( playlistName )+"]"
							#name = self.filterName( vid.title )
							pos = stream.default_filename.rindex(".")
							name = self.filterName( stream.default_filename[:pos] )
							filename += name
							filename += "("+str(link)+")"
							filename += stream.default_filename[pos:]
							filePath = os.path.join(self.downloadedFilesFolder,filename)
							stream.download( filename = filePath )
							if downloadOnlyAudio:
								self.messageBuffer.append('---converting to mp3: '+filename)
								audioclip = AudioFileClip(filePath)
								audioclip.write_audiofile(filePath[:-4]+'.mp3')
								self.messageBuffer.append('---removing: '+filename)
								audioclip.close()
								os.remove(filePath)
								
							ff.write('%s\n' % line)
						except Exception as ex:
							self.messageBuffer.append('error on: '+str(line))
							self.messageBuffer.append(str(ex))
							if line not in failedLinks:
								failedLinks.append(link)
								failedNames.append(name)
							#raise
		except KeyboardInterrupt:
			self.messageBuffer.append('Interrupted')
			with open(os.path.join(self.toDownloadLinksFolder,newLinksFile),'w',encoding='utf-8') as fff:
				fff.write('#%s\n' % sourceUrl)
				for line in lines:
					fff.write('%s \n' % line.strip('\n') )
				for link,name in zip(failedLinks,failedNames):
					fff.write('%s #%s\n' % (link,name))
		except Exception as ex:
			self.messageBuffer.append('error opening link file')
		
		with open(os.path.join(self.toDownloadLinksFolder,newLinksFile),'w',encoding='utf-8') as fff:
			fff.write('#%s\n' % sourceUrl)
			for line in lines:
				fff.write('%s \n' % line.strip('\n') )
			for link,name in zip(failedLinks,failedNames):
				fff.write('%s #%s\n' % (link,name))
				
		return None
	
	def updateList(self, filepath):
		"""update links from playlist"""
		#get url
		with open(filepath,'r',encoding='utf-8') as f:
			url = f.readline().strip('\n')
		if url[0] != "#":
			self.messageBuffer.append('no url for updating playlist present!')
			return None
		else:
			playlistUrl = url[1:]
		
		#get all links
		[links, playlistName, _] = self.session.collectLinks(playlistUrl)
		
		#remove already present links
		[downloadedLinks,downloadedNames] = self.loadLinks(filepath)
		
		for link in downloadedLinks:
			if link[0]=="#":
				continue#skip
			if link in links:
				links.remove(link)
		
		#save
		self.session.saveLinks(links, filepath, playlistUrl)
		
		return None
	
	def Mp4ToMp3(self, filename):
		self.messageBuffer.append('---converting to mp3: '+str(filename))
		audioclip = AudioFileClip(filename)
		audioclip.write_audiofile(filename[:-4]+'.mp3')
		self.messageBuffer.append('---removing: '+str(filename))
		os.remove(filename)
		audioclip.close()

class right_click_handler():
	def __init__(self, root):
		#right click menu
		self.m = tk.Menu(root, tearoff=0)
		self.m.add_command(label="Cut",command=self.doCut)
		self.m.add_command(label="Copy",command=self.doCopy)
		self.m.add_command(label="Paste",command=self.doPaste)
	def doCut(self):
		selected = self.element.selection_get()
		self.element.delete("sel.first", "sel.last")
		self.element.clipboard_clear()
		self.element.clipboard_append(selected)
		return
		
	def doCopy(self):
		selected = self.element.selection_get()
		self.element.clipboard_clear()
		self.element.clipboard_append(selected)
		return
		
	def doPaste(self):
		clipboard = self.element.clipboard_get()
		try:
			self.element.delete("sel.first", "sel.last")
		except:
			pass
		position = self.element.index(tk.INSERT)
		self.element.insert(position, clipboard)
		return
		
	def right_click_popup(self, event): 
		try:
			self.element = event.widget
			self.m.tk_popup(event.x_root, event.y_root)
		finally: 
			self.m.grab_release() 



### GUI
class Gui(tk.Tk):
	def __init__(self):
		self.session = DownloadHandler()
		
		super().__init__()
		rightClickHandler = right_click_handler(self)
		self.title("Youtube Downloader")

		log_frame = tk.Frame(self)
		log_frame.pack(side = tk.TOP, padx='5', pady='5')
		log_frame.rowconfigure(0, weight=1)
		log_frame.columnconfigure(0, weight=1)
		
		#log output
		self.textbox = tk.Text(log_frame, height=6)
		self.textbox.pack(side = tk.TOP)
		self.textbox.insert(tk.END, "...")
		self.textbox.config(state='disabled')
		scrollb = tk.Scrollbar(log_frame, command=self.textbox.yview)
		self.textbox.config(yscrollcommand=scrollb.set)
		
		useAuthentication_frame = tk.Frame(self)
		useAuthentication_frame.pack(side = tk.TOP, padx='5', pady='5')

		tk.Label(useAuthentication_frame, text="use authentication when downloading ?").pack(side = tk.TOP)

		#radiobutton use authentication
		self.useAuthentication = tk.IntVar()
		tk.Radiobutton(useAuthentication_frame,
					text="yes authenticate",
					padx = 20,
					variable=self.useAuthentication,
					value=True).pack(side = tk.LEFT)
		tk.Radiobutton(useAuthentication_frame,
					text="no authentication",
					padx = 20,
					variable=self.useAuthentication,
					value=False).pack(side = tk.LEFT)
		self.useAuthentication.set(False)
		
		removeDuplicateLinks_frame = tk.Frame(self)
		removeDuplicateLinks_frame.pack(side = tk.TOP, padx='5', pady='5')

		tk.Label(removeDuplicateLinks_frame, text="remove duplicate entries from previous lists of links ?").pack(side = tk.TOP)

		#radiobutton video/audio
		self.removeDuplicateLinks = tk.IntVar()
		tk.Radiobutton(removeDuplicateLinks_frame,
					text="remove",
					padx = 20,
					variable=self.removeDuplicateLinks,
					value=True).pack(side = tk.LEFT)
		tk.Radiobutton(removeDuplicateLinks_frame,
					text="keep",
					padx = 20,
					variable=self.removeDuplicateLinks,
					value=False).pack(side = tk.LEFT)
		self.removeDuplicateLinks.set(False)
		
		processingType_frame = tk.Frame(self)
		processingType_frame.pack(side = tk.TOP, padx='5', pady='5')

		tk.Label(processingType_frame, text="link extraction or media download ?").pack(side = tk.TOP)

		#radiobutton video/audio
		self.extractOnly = tk.IntVar()
		tk.Radiobutton(processingType_frame,
					text="extract",
					padx = 20,
					variable=self.extractOnly,
					value=True,
					command=self.hideMediaSelectionFrame).pack(side = tk.LEFT)
		tk.Radiobutton(processingType_frame,
					text="download",
					padx = 20,
					variable=self.extractOnly,
					value=False,
					command=self.showMediaSelectionFrame).pack(side = tk.LEFT)
		self.extractOnly.set(False)
		
		self.mediaSelection_frame = tk.Frame(self)
		self.mediaSelection_frame.pack(side = tk.TOP, padx='5', pady='5')

		tk.Label(self.mediaSelection_frame, text="for download select media output format:").pack(side = tk.TOP)

		#radiobutton video/audio -> filename video/audio
		self.audioOnly = tk.IntVar()
		tk.Radiobutton(self.mediaSelection_frame,
					text="audio",
					padx = 20,
					variable=self.audioOnly,
					value=True).pack(side = tk.LEFT)
		tk.Radiobutton(self.mediaSelection_frame,
					text="video",
					padx = 20,
					variable=self.audioOnly,
					value=False).pack(side = tk.LEFT)
		self.audioOnly.set(True)
		
		#----------
		
		#link	 -> extract/download
		self.link_frame = tk.Frame(self)
		self.link_frame.pack(side = tk.TOP, padx='5', pady='5')

		self.link = tk.StringVar()
		self.link_entry = tk.Entry(self.link_frame, textvariable = self.link,
								 font=('calibre',10,'normal'), width = 50)
		self.link_entry.pack(side = tk.LEFT, padx='5', pady='5')
		self.link_entry.bind("<Button-3>", rightClickHandler.right_click_popup)
		self.link_button = tk.Button(self.link_frame, command=self.processLink,
									 text='one Link', width = 14)
		self.link_button.pack(side = tk.LEFT, padx='5', pady='5')

		#playlist -> extract/download
		self.playlist_frame = tk.Frame(self)
		self.playlist_frame.pack(side = tk.TOP, padx='5', pady='5')

		self.playlist = tk.StringVar()
		self.playlist_entry = tk.Entry(self.playlist_frame, textvariable = self.playlist,
								 font=('calibre',10,'normal'), width = 50)
		self.playlist_entry.pack(side = tk.LEFT, padx='5', pady='5')
		self.playlist_entry.bind("<Button-3>", rightClickHandler.right_click_popup)
		self.playlist_button = tk.Button(self.playlist_frame, command=self.processPlaylist,
									 text='full Playlist', width = 14)
		self.playlist_button.pack(side = tk.LEFT, padx='5', pady='5')
		
		#channel	-> extract/download
		self.channel_frame = tk.Frame(self)
		self.channel_frame.pack(side = tk.TOP, padx='5', pady='5')

		self.channel = tk.StringVar()
		self.channel_entry = tk.Entry(self.channel_frame, textvariable = self.channel,
								 font=('calibre',10,'normal'), width = 50)
		self.channel_entry.pack(side = tk.LEFT, padx='5', pady='5')
		self.channel_entry.bind("<Button-3>", rightClickHandler.right_click_popup)
		self.channel_button = tk.Button(self.channel_frame, command=self.processChannel,
									text='Channel uploads', width = 14)
		self.channel_button.pack(side = tk.LEFT, padx='5', pady='5')
		
		#----------
		
		ttk.Separator(self, orient='horizontal').pack()
		
		#extracted Linklist	 -> download
		self.file_frame = tk.Frame(self)
		self.file_frame.pack(side = tk.TOP, padx='5', pady='5')

		self.file = tk.StringVar()
		self.file_entry = tk.Entry(self.file_frame, textvariable = self.file,
								 font=('calibre',10,'normal'), width = 50)
		self.file_entry.pack(side = tk.LEFT, padx='5', pady='5')
		self.file_entry.bind("<1>", self.browseFiles)
		self.file_button = tk.Button(self.file_frame, command=self.processLinkFile,
									 text='download specific extracted', width = 24)
		self.file_button.pack(side = tk.LEFT, padx='5', pady='5')

		#all Linklists	-> extract/download
		self.downloadAllFiles_frame = tk.Frame(self)
		self.downloadAllFiles_frame.pack(side = tk.TOP, padx='5', pady='5')

		self.downloadAllFiles_button = tk.Button(self.downloadAllFiles_frame, command=self.processAllLinkFiles,
									 text='download All extracted', width = 24)
		self.downloadAllFiles_button.pack(side = tk.LEFT, padx='5', pady='5')

		#all Linklists	-> update
		self.updateAllFiles_frame = tk.Frame(self)
		self.updateAllFiles_frame.pack(side = tk.TOP, padx='5', pady='5')

		self.updateAllFiles_button = tk.Button(self.updateAllFiles_frame, command=self.updatePlaylist,
									 text='update All extracted', width = 24)
		self.updateAllFiles_button.pack(side = tk.LEFT, padx='5', pady='5')

		#----------

#		self.link.set("")
#		self.playlist.set("")
#		self.channel.set("")
#		self.file.set("")
		
		self.updateTextbox()
		
	def updateTextbox(self):
		while len(self.session.messageBuffer):
			message = self.session.messageBuffer.pop()
			print(message)
			self.textbox.insert(tk.END, message )
		#restart function in 1s
		threading.Timer(1, self.updateTextbox).start()
	
	def hideMediaSelectionFrame(self):
		self.mediaSelection_frame.pack_forget()
			
	def showMediaSelectionFrame(self):
		self.mediaSelection_frame.pack(side = tk.TOP, padx='5', pady='5',
							before=self.link_frame)
		
	def browseFiles(self, event):
		filename = tk.filedialog.askopenfilename(initialdir = "./toDownloadLinks",
						title = "Select Link file",
						filetypes = (("Text files",
							"*.txt*"),
								 ("all files",
							"*.*")))
		self.file.set(filename)
		return None
	
	def processLink(self):
		linkUrl = str(self.link.get())
		vid = pytube.YouTube(linkUrl)
		channelName = vid.author
		channelUrl = vid.channel_url
		name = vid.title
		
		#request channel page
#		response = requests.get(channelUrl)
#		if response.status_code != 200:
#			self.messageBuffer.append("failed to load channel url to extract playlist")
#		response.raise_for_status()
#		body = response.text
		
		#extract playlist id
#		keyword = "\"browseId\":\"UC"
#		pos1 = body.find(keyword)+len(keyword)
#		pos2 = body.find("\"",pos1)
#		playlistUrl = "https://www.youtube.com/playlist?list=UU"
#		playlistUrl += body[pos1:pos2]
		
#		playlist = pytube.Playlist(playlistUrl)
#		links = playlist.video_urls
#		links = [self.session.filterId(link) for link in links]
#		playlistName = playlist.title
#		channelName = playlist.owner
		
		links = [self.session.filterId(linkUrl)]
		names = [self.session.filterName(name)]

		fileName = channelName+".txt"
		fileName = self.session.filterName(fileName)
		filePath = os.path.join(self.session.toDownloadLinksFolder,fileName)
		self.session.saveLinks(links, filePath, '-') #playlistUrl
		if self.removeDuplicateLinks.get():
			[duplicates,checkedLinks,allDuplicateFiles] = self.session.findDuplicateLinks(fileName)
			duplicateRemover = windowPopUp(duplicates,self.link)
			self.session.deleteDuplicateLinks(fileName,checkedLinks,allDuplicateFiles,duplicateRemover.keepLink,duplicateRemover.deleteLink)
		if self.extractOnly.get():
			self.textbox.insert(tk.END, "extracted link: "+linkUrl)
		else:
			self.textbox.insert(tk.END, "downloading link: "+linkUrl)
			audioOnly = self.audioOnly.get()
			authenticate = self.useAuthentication.get()
			self.session.downloadFiles(fileName, audioOnly, authenticate)
		
	def processPlaylist(self):
		playlistUrl = str(self.playlist.get())
		[links, playlistName, channelName] = self.session.collectLinks(playlistUrl)
		if playlistName[:13]=="Uploads from ":
			fileName = playlistName[13:]+".txt"
		else:
			fileName = playlistName+".txt"
		fileName = self.session.filterName(fileName)
		filePath = os.path.join(self.session.toDownloadLinksFolder,fileName)
		self.session.saveLinks(links, filePath, playlistUrl)
		if self.removeDuplicateLinks.get():
			[duplicates,checkedLinks,allDuplicateFiles] = self.session.findDuplicateLinks(fileName)
			duplicateRemover = windowPopUp(duplicates,...)
			self.session.deleteDuplicateLinks(fileName,checkedLinks,allDuplicateFiles,duplicateRemover.keepLink,duplicateRemover.deleteLink)
		if self.extractOnly.get():
			self.textbox.insert(tk.END, "extracted playlist: "+playlistName)
		else:
			self.textbox.insert(tk.END, "downloading playlist: "+playlistName)
			audioOnly = self.audioOnly.get()
			authenticate = self.useAuthentication.get()
			self.session.downloadFiles(fileName, audioOnly, authenticate)
	
	def processChannel(self):
		channelUrl = str(self.channel.get())
		[playlistUrl, channelName] = self.session.channelPlaylist(channelUrl)
		[links, playlistName, _] = self.session.collectLinks(playlistUrl)
		fileName = channelName+".txt"
		fileName = self.session.filterName(fileName)
		filePath = os.path.join(self.session.toDownloadLinksFolder,fileName)
		self.session.saveLinks(links, filePath, playlistUrl)
		if self.removeDuplicateLinks.get():
			[duplicates,checkedLinks,allDuplicateFiles] = self.session.findDuplicateLinks(fileName)
			duplicateRemover = windowPopUp(duplicates,...)
			self.session.deleteDuplicateLinks(fileName,checkedLinks,allDuplicateFiles,duplicateRemover.keepLink,duplicateRemover.deleteLink)
		if self.extractOnly.get():
			self.textbox.insert(tk.END, "extracted channel: "+playlistName)
		else:
			self.textbox.insert(tk.END, "downloading channel: "+playlistName)
			audioOnly = self.audioOnly.get()
			authenticate = self.useAuthentication.get()
			self.session.downloadFiles(fileName, audioOnly, authenticate)
	
	def processLinkFile(self):
		path = self.file.get()
		fileName = os.path.basename(path)
		fileName = self.session.filterName(fileName)
		self.textbox.insert(tk.END, "download extracted Links from: "+path)
		if self.removeDuplicateLinks.get():
			[duplicates,checkedLinks,allDuplicateFiles] = self.session.findDuplicateLinks(fileName)
			duplicateRemover = windowPopUp(duplicates,self.link)
			self.session.deleteDuplicateLinks(fileName,checkedLinks,allDuplicateFiles,duplicateRemover.keepLink,duplicateRemover.deleteLink)
		audioOnly = self.audioOnly.get()
		authenticate = self.useAuthentication.get()
		self.session.downloadFiles(fileName, audioOnly, authenticate)
		
	def processAllLinkFiles(self):
		fileNames = self.session.listOfAllLinks(self.session.toDownloadLinksFolder)
		self.textbox.insert(tk.END, "download all extracted Links from: "+str(len(fileNames))+" files.")
		for path in fileNames:
			self.textbox.insert(tk.END, "download extracted Links from: "+path)
			fileName = os.path.basename(path)
			if fileName=="blackList.txt":
				continue#skip
			if self.removeDuplicateLinks.get():
				[duplicates,checkedLinks,allDuplicateFiles] = self.session.findDuplicateLinks(fileName)
				duplicateRemover = windowPopUp(duplicates,self.link)
				self.session.deleteDuplicateLinks(fileName,checkedLinks,allDuplicateFiles,duplicateRemover.keepLink,duplicateRemover.deleteLink)
			audioOnly = self.audioOnly.get()
			authenticate = self.useAuthentication.get()
			self.session.downloadFiles(fileName, audioOnly, authenticate)

	def updatePlaylist(self):
		for (dirpath, dirnames, filenames) in os.walk(self.session.downloadedLinksFolder):
			for filename in filenames:
				filepath = os.path.join(dirpath,filename)
				self.session.updateList(filepath)
		for (dirpath, dirnames, filenames) in os.walk(self.session.toDownloadLinksFolder):
			for filename in filenames:
				filepath = os.path.join(dirpath,filename)
				self.session.updateList(filepath)



class windowPopUp(tk.Toplevel):
	keepLink = dict() #list of filePaths where to keep link
	deleteLink = dict() #list of filePaths where to delete link from
	
	def __init__(self, duplicates, var):
		tk.Toplevel.__init__(self)
		self.title("please select where to keep duplicate url")
		self.geometry('400x300')
		#self.minsize(600, 400)
		#self.maxsize(425, 250)
		self.rowconfigure(0, weight=0)
		self.rowconfigure(1, weight=1)
		self.columnconfigure(0, weight=1)
		
		#canvas & scrollbar - root
		canvas = tk.Canvas(self)
		scroll = tk.Scrollbar(self, orient="vertical")
		
		#place canvas & scrollbar
		#scroll.grid(row=0, column=1, sticky="nes") #grid#
		scroll.pack(side="right", fill="y") #pack#
		#canvas.grid(row=0, column=0, sticky="nsew") #grid#
		canvas.pack(fill="both", expand=1, anchor="nw") #pack#
		
		#enable scrolling
		scroll.configure(command=canvas.yview)
		canvas.configure(yscrollcommand=scroll.set)
		canvas.bind("<Enter>",
				lambda _: canvas.bind_all('<MouseWheel>', 
						lambda e: canvas.config( canvas.yview_scroll(int(-1*(e.delta/120)), "units") )
				)
		)
		
		#frame for content - canvas
		frame = tk.Frame(canvas, background="#FFFFFF")
		gridrow = 0
		
		#label - frame
		title1 = tk.Label(frame, text='title')
		#title1.grid(row=gridrow, column=0, sticky="n") #grid#
		title1.pack(fill=tk.BOTH, expand=tk.TRUE, anchor="n") #pack#
		gridrow += 1
		
		#for python 3.9+ (dict order constant)
		self.duplicates = duplicates
		self.selection = dict()
		for link,presentFiles in self.duplicates.items():
			#button_frame = tk.Frame(frame)
			#button_frame.grid(row=gridrow, column=0, sticky="") #grid#
			#button_frame.pack(anchor="center") #pack#
			gridrow += 1
			
			#link
			linkLabel = tk.Label(frame, text=str(link))
			#linkLabel.grid(row=gridrow, column=0, sticky="") #grid#
			linkLabel.pack(fill=tk.BOTH, expand=tk.TRUE, anchor="center") #pack#
			gridrow += 1
			
			maxcol = 0
			#//present in files:
			self.selection[link] = tk.IntVar()
			for pos in range(len(presentFiles)):
				radiobutton = tk.Radiobutton(frame,
					text=str(presentFiles[pos]),
					padx = 4,
					variable=self.selection[link],
					value=pos)
				#radiobutton.grid(row=gridrow, column=pos, sticky="w") #grid#
				radiobutton.pack(expand=tk.FALSE, anchor="center") #pack#
			if pos > maxcol:
				maxcol = pos
			gridrow += 1
			self.selection[link].set(0)
		gridrow += 1
		
		#button - frame
		#submitButton = tk.Button(frame, text="done", command=self.destroy)
		submitButton = tk.Button(frame, text="done", command=self.submit)
		#submitButton.grid(row=gridrow, column=0, sticky="s") #grid#
		submitButton.pack(fill=tk.BOTH, expand=tk.TRUE, anchor="s") #pack#
		gridrow += 1
		
		#add frame to canvas - canvas
		wrapFrame = canvas.create_window((0,0), window=frame, anchor="nw")
		
		def onFrameConfigure(canvas):
			canvas.configure(scrollregion=canvas.bbox("all")) #show scroll bar
			canvas.itemconfigure(wrapFrame, width=canvas.winfo_width()) #correct canvas size
			return None
		canvas.bind("<Configure>", lambda e: onFrameConfigure(canvas))
		
		# expand canvas
		#self.columnconfigure((0), weight=1) #grid#
		#self.rowconfigure((0), weight=1) #grid#
		
		# expand frame
		#frame.columnconfigure((0), weight=1) #grid#
		#frame.rowconfigure((0), weight=1) #grid#

		self.transient(self.master) #same visibility as window below
		self.grab_set()  #this window on top
		self.wait_window(self) #continue after window closes
	
	def submit(self):
		for link,presentFiles in self.duplicates.items():
			self.keepLink[link] = presentFiles.pop( self.selection[link].get() )
			self.deleteLink[link] = presentFiles
		self.destroy()
		return None

if __name__ == '__main__':
	App = Gui().mainloop()
