#!/usr/bin/python

import wx
import wx.lib.inspection
from wx.lib.pubsub import pub
import random
import threading

"""
Hierarchy:

vertical sizer
    horizontal sizer for specific classes
        Static box surrounding the specific class controls
        Classes list box, double click = generate that class
        Generate button?
    vertical sizer for randoms
        static box surrounding random tools
        horizontal sizer
            Label for text control
            Text control for number of random characters
        Generate button
"""

quips = ["All these guys are gonna die anyway",
         "A 1 is good, right?",
         "HOW many hit points?",
         "No, I'm sure those spells will be useful",
         "Don't get too attached",
         "The last 13 guys? They didn't have what it takes. But you? YOU'VE got the stuff.",
         "Intelligence 8? This character is just like you!",
         "Old age looked boring anyway"]

title_text = "Lament - " + random.choice(quips)


class LamentFrame(wx.Frame):
    def __init__(self, parent=None, *args, **kwargs):
        wx.Frame.__init__(self, parent,
                          size=(650, 600),
                          title=title_text,
                          style=wx.DEFAULT_FRAME_STYLE,
                          *args, **kwargs)
        self.panel = wx.Panel(self)
        self.specific_generate = wx.Button(self.panel, label="Generate")
        self.random_generate = wx.Button(self.panel, label="HOPE FOR THE BEST")

        classes = ['Cleric', 'Fighter', 'Magic-User', 'Specialist', 'Dwarf', 'Elf', 'Halfling']
        self.class_list = wx.ListBox(self.panel, choices=classes, name="Classes")

        self.initUI()
        self.statusbar = self.CreateStatusBar()

        pub.subscribe(self.update_statusbar, "status.update")
        pub.subscribe(self.update_dialog, "dialog")

        pub.subscribe(self.update_progress, "progress.update")

        self.Center()
        self.Show(True)

    def initUI(self):
        menubar = wx.MenuBar()
        file_menu = wx.Menu()
        about_menu = wx.Menu()

        quit_item = file_menu.Append(wx.ID_EXIT, '&Quit\tAlt+F4', 'Close Lament')
        self.Bind(wx.EVT_MENU, self.onClose, quit_item)
        menubar.Append(file_menu, '&File')

        about_item = about_menu.Append(wx.ID_ABOUT, '&About', 'Self-aggrandizement')
        self.Bind(wx.EVT_MENU, self.onAbout, about_item)
        menubar.Append(about_menu, '&About')

        self.SetMenuBar(menubar)
        sizer = wx.BoxSizer(wx.VERTICAL)

        class_label = wx.StaticBox(self.panel, label="Generate a specific class")
        clabel_font = wx.Font(wx.FontInfo(11).Italic())
        class_label.SetFont(clabel_font)

        specifics_sizer = wx.StaticBoxSizer(class_label, wx.HORIZONTAL)

        list_font = wx.Font(wx.FontInfo(16).FaceName("IM FELL English PRO"))
        self.class_list.SetFont(list_font)
        self.Bind(wx.EVT_LISTBOX_DCLICK, self.generateSpecific, self.class_list)

        cgen_font = wx.Font(wx.FontInfo(15).FaceName("tommy alee"))
        self.specific_generate.SetFont(cgen_font)
        self.Bind(wx.EVT_BUTTON, self.generateSpecific, self.specific_generate)

        specifics_sizer.Add(self.class_list,
                            proportion=1,
                            flag=wx.EXPAND | wx.ALL,
                            border=15)
        specifics_sizer.Add(self.specific_generate,
                            flag=wx.ALIGN_RIGHT | wx.ALIGN_BOTTOM | wx.ALL,
                            border=15)

        sizer.Add(specifics_sizer,
                  flag=wx.EXPAND | wx.ALL | wx.ALIGN_TOP,
                  border=10)

        random_label = wx.StaticBox(self.panel, label="Generate a number of random characters")
        rlabel_font = wx.Font(wx.FontInfo(11).Italic())
        random_label.SetFont(rlabel_font)
        random_sizer = wx.StaticBoxSizer(random_label, wx.VERTICAL)

        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        number_label = wx.StaticText(self.panel, label="How many random characters do you want?")
        nlabel_font = wx.Font(wx.FontInfo(10))
        number_label.SetFont(nlabel_font)
        self.number = wx.TextCtrl(self.panel, value="1", style=wx.TE_PROCESS_ENTER)
        self.Bind(wx.EVT_TEXT_ENTER, self.generateRandom, self.number)

        hsizer.Add(number_label,
                   flag=wx.ALL,
                   border=15)
        hsizer.Add(self.number,
                   flag=wx.ALL | wx.EXPAND,
                   border=15)

        # random_generate = wx.Button(self.panel, label="HOPE FOR THE BEST")
        rgen_font = wx.Font(wx.FontInfo(15).FaceName("tommy alee"))
        self.random_generate.SetFont(rgen_font)
        self.Bind(wx.EVT_BUTTON, self.generateRandom, self.random_generate)

        random_sizer.Add(hsizer,
                         flag=wx.ALIGN_CENTER_HORIZONTAL,
                         border=10)
        random_sizer.Add(self.random_generate,
                         flag=wx.ALIGN_CENTER_HORIZONTAL | wx.ALL,
                         border=15)

        sizer.Add(random_sizer,
                  flag=wx.ALIGN_BOTTOM | wx.EXPAND | wx.ALL,
                  border=10)

        credit_text = "This program makes use of the excellent OSR character generator located at \n" \
                      "http://character.totalpartykill.ca/lotfp. Much thanks to funkaoshi, who wrote it."
        credit = wx.StaticText(self.panel, label=credit_text)
        credit_font = wx.Font(wx.FontInfo(9).Italic())
        credit.SetFont(credit_font)

        sizer.Add(credit,
                  flag=wx.ALIGN_CENTER_HORIZONTAL | wx.ALIGN_BOTTOM | wx.ALL,
                  border=10)

        self.panel.SetSizer(sizer)

    def onClose(self, event):
        self.Close()

    def onAbout(self, event):
        pass

    def update_dialog(self, title, msg):
        dlg = wx.MessageDialog(self.panel, style=wx.OK, caption=title, message=msg)
        dlg.ShowModal()
        dlg.Destroy()

    def update_progress(self, msg, value):
        self.progress.Update(value=value, newmsg=msg)

    def update_statusbar(self, msg):
        self.statusbar.SetStatusText(msg)

    def generateSpecific(self, event):
        pub.sendMessage("status.update", msg="Generating one %s..." % self.class_list.GetStringSelection())
        self.progress = wx.ProgressDialog(title="Wait for it...", message="Generating characters...")

        button = event.GetEventObject()
        button.Disable()

        gen_thread = threading.Thread(target=self.lament_specific,
                                      name="specific_gen",
                                      kwargs={'desired_class': self.class_list.GetStringSelection(), 'number': 1})
        gen_thread.start()

    def lament_specific(self, desired_class, number):
        pub.sendMessage("specific.generate", desired_class=desired_class, number=number)
        wx.CallAfter(self.progress.Destroy)
        wx.CallAfter(self.specific_generate.Enable)
        wx.CallAfter(pub.sendMessage, "dialog",
                     title="Done at last!",
                     msg="Boom. %s characters, one PDF. Ready to print. You're welcome."
                         "\n\nP.S. Don't forget the final PDF is A4." % str(number))

    def generateRandom(self, event):
        pub.sendMessage("status.update", msg="Generating %s randos..." % self.number.GetValue())
        self.progress = wx.ProgressDialog(title="Wait for it...", message="Generating characters...")

        button = event.GetEventObject()
        button.Disable()

        gen_thread = threading.Thread(target=self.lament_random,
                                      name="random_gen",
                                      kwargs={'number': self.number.GetValue()})
        gen_thread.start()

    def lament_random(self, number):
        pub.sendMessage("random.generate", number=int(number))
        wx.CallAfter(self.progress.Destroy)
        wx.CallAfter(self.random_generate.Enable)
        wx.CallAfter(pub.sendMessage, "dialog",
                     title="Done at last!",
                     msg="Boom. %s characters, one PDF. Ready to print. You're welcome."
                         "\n\nP.S. Don't forget the final PDF is A4." % str(number))


"""
if __name__ == "__main__":
    app = wx.App()
    LamentFrame(None)
    # wx.lib.inspection.InspectionTool().Show()
    app.MainLoop()
"""
