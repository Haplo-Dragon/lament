#!/usr/bin/python

import wx
import wx.lib.inspection

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


#title_text = "Lament - A random character sheet generator for LotFP (Mockup)"
title_text = "Lament - Fills PDF sheets with random LotFP characters (Mockup)"



class LamentFrame(wx.Frame):
    def __init__(self, parent=None):
        wx.Frame.__init__(self, parent,
                          size=(640, 525),
                          title=title_text,
                          style=wx.DEFAULT_FRAME_STYLE)

        self.initUI()
        self.Center()
        self.Show(True)

    def initUI(self):
        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)

        classes = ['Cleric', 'Fighter', 'Magic-User', 'Specialist', 'Dwarf', 'Elf', 'Halfling']
        class_label = wx.StaticBox(panel, label="Generate a specific class")
        clabel_font = wx.Font(wx.FontInfo(11).Italic())
        class_label.SetFont(clabel_font)

        specifics_sizer = wx.StaticBoxSizer(class_label, wx.HORIZONTAL)

        class_list = wx.ListBox(panel, choices=classes, name="Classes")
        list_font = wx.Font(wx.FontInfo(16).FaceName("IM FELL English PRO"))
        class_list.SetFont(list_font)
        specific_generate = wx.Button(panel, label="Generate")
        cgen_font = wx.Font(wx.FontInfo(15).FaceName("tommy alee"))
        specific_generate.SetFont(cgen_font)

        specifics_sizer.Add(class_list,
                            proportion=1,
                            flag=wx.EXPAND | wx.ALL,
                            border=15)
        specifics_sizer.Add(specific_generate,
                            flag=wx.ALIGN_RIGHT | wx.ALIGN_BOTTOM | wx.ALL,
                            border=15)

        sizer.Add(specifics_sizer,
                  flag=wx.EXPAND | wx.ALL | wx.ALIGN_TOP,
                  border=10)

        random_label = wx.StaticBox(panel, label="Generate a number of random characters")
        rlabel_font = wx.Font(wx.FontInfo(11).Italic())
        random_label.SetFont(rlabel_font)
        random_sizer = wx.StaticBoxSizer(random_label, wx.VERTICAL)

        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        number_label = wx.StaticText(panel, label="How many random characters do you want?")
        nlabel_font = wx.Font(wx.FontInfo(10))
        number_label.SetFont(nlabel_font)
        number = wx.TextCtrl(panel, value="1", style=wx.TE_PROCESS_ENTER)
        hsizer.Add(number_label,
                   flag=wx.ALL,
                   border=15)
        hsizer.Add(number,
                   flag=wx.ALL | wx.EXPAND,
                   border=15)

        random_generate = wx.Button(panel, label="HOPE FOR THE BEST")
        rgen_font = wx.Font(wx.FontInfo(15).FaceName("tommy alee"))
        random_generate.SetFont(rgen_font)

        random_sizer.Add(hsizer,
                         flag=wx.ALIGN_CENTER_HORIZONTAL,
                         border=10)
        random_sizer.Add(random_generate,
                         flag=wx.ALIGN_CENTER_HORIZONTAL | wx.ALL,
                         border=15)

        sizer.Add(random_sizer,
                  flag=wx.ALIGN_BOTTOM | wx.EXPAND | wx.ALL,
                  border=10)

        credit_text = "This program makes use of the excellent OSR character generator located at \n" \
                      "http://character.totalpartykill.ca/lotfp. Much thanks to funkaoshi, who wrote it."
        credit = wx.StaticText(panel, label=credit_text)
        credit_font = wx.Font(wx.FontInfo(9).Italic())
        credit.SetFont(credit_font)

        sizer.Add(credit,
                  flag=wx.ALIGN_CENTER_HORIZONTAL | wx.ALIGN_BOTTOM | wx.ALL,
                  border=10)

        panel.SetSizer(sizer)


if __name__ == "__main__":
    app = wx.App()
    LamentFrame(None)
    # wx.lib.inspection.InspectionTool().Show()
    app.MainLoop()
