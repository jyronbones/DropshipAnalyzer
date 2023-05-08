import os
import threading
import tkinter as tk
import tkinter.messagebox
import pandas as pd
from matplotlib import pylab
from pyodbc import ProgrammingError
import customtkinter
from tkinter import filedialog as fd, ttk
from tkinter.messagebox import showinfo
from tkinter import messagebox
import matplotlib.pyplot as plt
from amazon_scrape import scrape as amazon_scrape
from baba_scrape import scrape as baba_scrape
from db import delete_tables, df_to_temp_amazon_table, df_to_temp_baba_table, temp_to_main

customtkinter.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"
customtkinter.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"
product_list = []
amazon_headers = ['product_title', 'product_price', 'regular_price', 'product_shipping',
                  'product_rating', 'amazon_prime', 'review_count', 'product_link',
                  'item_searched']
alibaba_headers = ['product_title', 'product_price', 'price_range', 'approx_cdn_price', 'product_shipping',
                   'product_min_qty', 'product_rating', 'supplier_verified', 'review_count', 'common_review',
                   'product_link', 'item_searched']
amazon_df = pd.DataFrame(columns=amazon_headers)
alibaba_df = pd.DataFrame(columns=alibaba_headers)
global e, selection, is_on
is_on = False


def get_amazon_df(prod_df):
    global amazon_df
    amazon_df = pd.concat([amazon_df, prod_df], ignore_index=True)


def get_alibaba_df(prod_df):
    global alibaba_df
    alibaba_df = pd.concat([alibaba_df, prod_df], ignore_index=True)
    alibaba_df.rename(columns={'product_price': 'us_price', 'approx_cdn_price': 'product_price'}, inplace=True)


def select_file():
    filetypes = (
        ('text files', '*.txt'),
        ('All files', '*.txt')
    )

    filename = fd.askopenfilename(
        title='Open a file',
        initialdir='/',
        filetypes=filetypes)

    showinfo(
        title='Selected File',
        message=filename
    )
    return filename


def find_products():
    if len(product_list) == 0:
        messagebox.showinfo("Empty Products List", "Import a products text file first\n\tOR\nEnter a product to search")
    else:
        amz_thread = threading.Thread(target=scrape_amazon)
        baba_thread = threading.Thread(target=scrape_alibaba)
        amz_thread.start()
        baba_thread.start()
        amz_thread.join()
        baba_thread.join()


def scrape_amazon():
    global amazon_df
    amazon_df = amazon_scrape(product_list)
    get_amazon_df(amazon_df)


def scrape_alibaba():
    global alibaba_df
    alibaba_df = baba_scrape(product_list)
    get_alibaba_df(alibaba_df)


class App(customtkinter.CTk):
    WIDTH = 780
    HEIGHT = 520

    def __init__(self):
        super().__init__()

        self.iconbitmap(default='rocket.ico')

        menubar = tkinter.Menu(self, background='#A6D4F9', foreground='white', activebackground='black',
                               activeforeground='white')
        file = tkinter.Menu(menubar, tearoff=0, background='black', foreground='white')
        file.add_separator()
        file.add_command(label="Import Products from File", command=self.import_button_event)
        file.add_command(label="Save")
        file.add_command(label="Save as")
        file.add_separator()
        file.add_command(label="Exit", command=self.on_closing)
        menubar.add_cascade(label="File", menu=file)
        file.add_separator()

        edit = tkinter.Menu(menubar, tearoff=0, background='black', foreground='white')
        edit.add_separator()
        edit.add_command(label="Undo")
        edit.add_separator()
        edit.add_command(label="Cut")
        edit.add_command(label="Copy")
        edit.add_command(label="Paste")
        menubar.add_cascade(label="Edit", menu=edit)
        appearance = tkinter.Menu(edit, tearoff=0, background='black', foreground='white')
        appearance.add_separator()
        appearance.add_command(label="Dark Mode", command=self.dark_mode)
        appearance.add_command(label="Light Mode", command=self.light_mode)
        appearance.add_separator()
        edit.add_separator()
        edit.add_cascade(label="Appearance", menu=appearance)
        edit.add_separator()

        database = tkinter.Menu(menubar, tearoff=0, background='black', foreground='white')
        database.add_separator()
        database.add_command(label="Export to Database", command=self.export_to_db)
        database.add_command(label="Move Data from Temp Tables to Main Tables", command=self.temp_to_main_tables)
        database.add_command(label="Delete Temp Tables", command=self.remove_temp_tables)
        database.add_separator()
        menubar.add_cascade(label="Database", menu=database)

        help = tkinter.Menu(menubar, tearoff=0, background='black', foreground='white')
        help.add_separator()
        help.add_command(label="About", command=self.about)
        help.add_separator()
        menubar.add_cascade(label="Help", menu=help)

        self.config(menu=menubar)

        self.title("Dropship Product Analyzer")
        self.geometry(f"{App.WIDTH}x{App.HEIGHT}")
        self.protocol("WM_DELETE_WINDOW", self.on_closing)  # call .on_closing() when app gets closed

        # ============ create two frames ============

        # configure grid layout (2x1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.frame_left = customtkinter.CTkFrame(master=self,
                                                 width=180,
                                                 corner_radius=0)
        self.frame_left.grid(row=0, column=0, sticky="nswe")

        self.frame_right = customtkinter.CTkFrame(master=self)
        self.frame_right.grid(row=0, column=1, sticky="nswe", padx=20, pady=20)

        # ============ frame_left ============

        # configure grid layout (1x11)
        self.frame_left.grid_rowconfigure(0, minsize=10)  # empty row with minsize as spacing
        self.frame_left.grid_rowconfigure(5, weight=1)  # empty row as spacing
        self.frame_left.grid_rowconfigure(8, minsize=20)  # empty row with minsize as spacing
        self.frame_left.grid_rowconfigure(11, minsize=10)  # empty row with minsize as spacing

        self.label_1 = customtkinter.CTkLabel(master=self.frame_left,
                                              text="Menu",
                                              text_font=("Roboto Medium", -16))  # font name and size in px
        self.label_1.grid(row=1, column=0, pady=10, padx=10)

        self.button_2 = customtkinter.CTkButton(master=self.frame_left,
                                                text="Find Products",
                                                command=self.product_search_on_click)
        self.button_2.grid(row=2, column=0, pady=10, padx=20)

        self.button_1 = customtkinter.CTkButton(master=self.frame_left,
                                                text="Display Alibaba Results",
                                                command=self.display_baba_results)
        self.button_1.grid(row=3, column=0, pady=10, padx=20)

        self.display_amz_button = customtkinter.CTkButton(master=self.frame_left,
                                                          text="Display Amazon Results",
                                                          command=self.display_amazon_results)
        self.display_amz_button.grid(row=4, column=0, pady=10, padx=20)

        self.button_3 = customtkinter.CTkButton(master=self.frame_left,
                                                text="Price/Review Plot",
                                                command=self.price_plot_click)
        self.button_3.grid(row=5, column=0, pady=10, padx=20)

        self.reset = customtkinter.CTkButton(master=self.frame_left,
                                             text="Reset",
                                             command=self.restart)
        self.reset.grid(row=8, column=0, pady=10, padx=20)

        self.label_mode = customtkinter.CTkLabel(master=self.frame_left, text="Appearance Mode:")
        self.label_mode.grid(row=9, column=0, pady=0, padx=20, sticky="w")

        self.optionmenu_1 = customtkinter.CTkOptionMenu(master=self.frame_left,
                                                        values=["Light", "Dark", "System"],
                                                        command=self.change_appearance_mode)
        self.optionmenu_1.grid(row=10, column=0, pady=10, padx=20, sticky="w")

        # ============ frame_right ============

        # configure grid layout (3x7)
        self.frame_right.rowconfigure((0, 1, 2, 3), weight=1)
        self.frame_right.rowconfigure(7, weight=10)
        self.frame_right.columnconfigure((0, 1), weight=1)
        self.frame_right.columnconfigure(2, weight=0)

        self.frame_info = customtkinter.CTkFrame(master=self.frame_right)
        self.frame_info.grid(row=0, column=0, columnspan=2, rowspan=4, pady=20, padx=20, sticky="nsew")

        # ============ frame_info ============

        # configure grid layout (1x1)
        self.frame_info.rowconfigure(0, weight=1)
        self.frame_info.columnconfigure(0, weight=1)
        # new_win = tkinter.Toplevel(self)
        # new_win.title("Qeury Results")
        # new_win.geometry("600x250")
        # Label(new_win, text="Hello There!", font=('Georgia 15 bold')).pack(pady=30)
        self.label_info_1 = customtkinter.CTkLabel(master=self.frame_info,
                                                   text="Welcome to the Dropship Product Analyzer" +
                                                        "\n" +
                                                        "",
                                                   height=300,
                                                   width=300,
                                                   corner_radius=6,  # <- custom corner radius
                                                   fg_color=("white", "gray38"),  # <- custom tuple-color
                                                   justify=tkinter.LEFT)
        self.label_info_1.grid(column=0, row=0, sticky="nwe", padx=15, pady=15)

        self.progress_label = customtkinter.CTkLabel(master=self.frame_info,
                                                     text="",
                                                     text_font=("Roboto Medium", -12))
        self.progress_label.grid(row=1, column=0, pady=10, padx=10)
        # self.label_1 = customtkinter.CTkLabel(master=self.frame_left,
        #                                       text="Menu",
        #                                       text_font=("Roboto Medium", -16))  # font name and size in px
        # self.label_1.grid(row=1, column=0, pady=10, padx=10)
        style = ttk.Style()
        style.theme_use('alt')
        style.configure("black.Horizontal.TProgressbar", foreground='white', background='black')
        self.progress_bar = ttk.Progressbar(master=self.frame_info, style="black.Horizontal.TProgressbar",
                                            orient="horizontal", length=200, mode="indeterminate")
        self.progress_bar.grid(row=2, column=0, sticky="ew", padx=15, pady=15)
        # self.progressbar = customtkinter.CTkProgressBar(master=self.frame_info)
        # self.progressbar.grid(row=1, column=0, sticky="ew", padx=15, pady=15)

        # ============ frame_right ============

        self.radio_var = tkinter.IntVar(value=0)

        self.label_radio_group = customtkinter.CTkLabel(master=self.frame_right,
                                                        text="Configurations:")
        self.label_radio_group.grid(row=0, column=2, columnspan=1, pady=20, padx=10, sticky="")

        self.radio_button_1 = customtkinter.CTkRadioButton(master=self.frame_right,
                                                           variable=self.radio_var,
                                                           text="Filter by Product Price",
                                                           value=0)
        self.radio_button_1.grid(row=1, column=2, pady=10, padx=20, sticky="n")

        self.radio_button_2 = customtkinter.CTkRadioButton(master=self.frame_right,
                                                           variable=self.radio_var,
                                                           text="Filter by Review Count",
                                                           value=1)
        self.radio_button_2.grid(row=2, column=2, pady=10, padx=20, sticky="n")

        self.radio_button_3 = customtkinter.CTkRadioButton(master=self.frame_right,
                                                           variable=self.radio_var,
                                                           text="Filter by Product Rating",
                                                           value=2)
        self.radio_button_3.grid(row=3, column=2, pady=10, padx=20, sticky="n")
        # self.slider_1 = customtkinter.CTkSlider(master=self.frame_right,
        #                                         from_=0,
        #                                         to=1,
        #                                         number_of_steps=3,
        #                                         command=self.progressbar.set)
        # self.slider_1.grid(row=4, column=0, columnspan=2, pady=10, padx=20, sticky="we")

        # self.slider_2 = customtkinter.CTkSlider(master=self.frame_right,
        #                                         command=self.progressbar.set)
        # self.slider_2.grid(row=5, column=0, columnspan=2, pady=10, padx=20, sticky="we")

        self.switch_1 = customtkinter.CTkSwitch(master=self.frame_right,
                                                text="Cancel Noise", command=self.switch)
        self.switch_1.grid(row=4, column=2, columnspan=1, pady=10, padx=20, sticky="we")

        # self.switch_2 = customtkinter.CTkSwitch(master=self.frame_right,
        #                                         text="CTkSwitch")
        # self.switch_2.grid(row=5, column=2, columnspan=1, pady=10, padx=20, sticky="we")

        self.combobox_1 = customtkinter.CTkComboBox(master=self.frame_right,
                                                    values=["Lowest to Highest", "Highest to Lowest"])
        self.combobox_1.grid(row=6, column=2, columnspan=1, pady=10, padx=20, sticky="we")

        self.show_var = tk.IntVar(value=0)

        self.radio_show_all_button = customtkinter.CTkRadioButton(master=self.frame_right,
                                                                  variable=self.show_var,
                                                                  text="Show All Products",
                                                                  value=0)
        self.radio_show_all_button.grid(row=6, column=0, pady=10, padx=20, sticky="w")
        self.radio_show_top_5_button = customtkinter.CTkRadioButton(master=self.frame_right,
                                                                    variable=self.show_var,
                                                                    text="Show Top 5",
                                                                    value=1)
        self.radio_show_top_5_button.grid(row=6, column=1, pady=10, padx=20, sticky="w")
        # self.check_box_1 = customtkinter.CTkCheckBox(master=self.frame_right,
        #                                              text="CHECK BOX 1")
        # self.check_box_1.grid(row=6, column=0, pady=10, padx=20, sticky="w")

        # self.check_box_2 = customtkinter.CTkCheckBox(master=self.frame_right,
        #                                              text="Show All Products")
        # self.check_box_2.grid(row=6, column=1, pady=10, padx=20, sticky="w")

        self.entry = customtkinter.CTkEntry(master=self.frame_right,
                                            width=120,
                                            placeholder_text="Enter product to search")
        self.entry.grid(row=8, column=0, columnspan=2, pady=20, padx=20, sticky="we")

        self.button_5 = customtkinter.CTkButton(master=self.frame_right,
                                                text="Search Products",
                                                border_width=2,  # <- custom border_width
                                                fg_color=None,  # <- no fg_color
                                                command=self.get_product_entry)  # command=self.search_products_on_click)
        self.button_5.grid(row=8, column=2, columnspan=1, pady=0, padx=0, sticky="we")
        self.clear_button = customtkinter.CTkButton(master=self.frame_right,
                                                    text="Clear Text",
                                                    border_width=2,
                                                    fg_color=None,
                                                    command=self.clear_text)
        self.clear_button.grid(row=9, column=0, columnspan=1, pady=0, padx=20, sticky="we")

        # set default values
        self.optionmenu_1.set("Dark")
        # self.button_3.configure(state="disabled", text="Reset")
        self.combobox_1.set("Sorting Options")
        self.radio_button_1.select()
        self.display_amz_button.configure(state=tk.DISABLED)
        self.button_1.configure(state=tk.DISABLED)
        self.button_2.configure(state=tk.DISABLED)
        # self.slider_1.set(0.2)
        # self.slider_2.set(0.7)
        # self.progressbar.set(0.5)
        # self.switch_2.select()
        # self.radio_button_3.configure(state=tkinter.DISABLED)
        # self.check_box_1.configure(state=tkinter.DISABLED, text="Show Top 5")
        # self.check_box_2.select()

    def import_button_event(self):
        global filename
        filename = ''
        try:
            filename = fd.askopenfilename()
            if filename.endswith('.txt'):
                with open(filename) as file:
                    lines = file.readlines()
                    lines = [line.rstrip() for line in lines]
                    product_list.extend(lines)
                    self.progress_label.configure(text="Successfully imported products file")
                    self.button_2.configure(state=tk.ACTIVE)
            elif filename == '':
                messagebox.showinfo("File not Specified", "No file Selected")
                self.progress_label.configure(text="File not specified")
            else:
                messagebox.showinfo("Wrong File Type", "Import only .txt files")
                self.progress_label.configure(text="invalid file format")
        except FileNotFoundError:
            print(f'FileNotFoundError: {filename}')

    def product_search_on_click(self):
        global submit_thread
        self.button_2.configure(state=tkinter.DISABLED)
        self.button_5.configure(state=tkinter.DISABLED)
        self.button_1.configure(state=tkinter.DISABLED)
        self.display_amz_button.configure(state=tkinter.DISABLED)
        submit_thread = threading.Thread(target=find_products)
        submit_thread.daemon = True
        self.progress_bar.start()
        self.progress_label.configure(text="Please wait for product search to finish...")
        submit_thread.start()
        self.after(20, self.check_submit_thread)

    def check_submit_thread(self):
        if submit_thread.is_alive():
            self.after(20, self.check_submit_thread)
        else:
            if len(product_list) == 0:
                self.progress_label.configure(text="No products to search")
                self.button_2.configure(state=tkinter.ACTIVE)
                self.button_5.configure(state=tkinter.ACTIVE)
                self.button_1.configure(state=tkinter.ACTIVE)
                self.display_amz_button.configure(state=tkinter.ACTIVE)
                self.progress_bar.stop()
            else:
                self.progress_label.configure(text="Product search finished")
                self.progress_bar.stop()
                self.button_2.configure(state=tkinter.ACTIVE)
                self.button_5.configure(state=tkinter.ACTIVE)
                self.button_1.configure(state=tkinter.ACTIVE)
                self.display_amz_button.configure(state=tkinter.ACTIVE)

    def about(self):
        messagebox.showinfo("About", "Dropshipping Product Analyzer\nCopyright © 2022\nCreated by Byron Jones")

    def amazon_price_review_plot(self):
        global amazon_df
        self.progress_label.configure(text="Scatterplots displayed")
        amazon_df.sort_values(by=['product_price', 'review_count'])
        amazon_df.plot(kind='scatter', x='product_price', y='review_count', color='red')
        plt.legend(loc='best', fontsize=11)
        plt.xlabel('Review Count')
        plt.ylabel('Price')
        fig = pylab.gcf()
        fig.canvas.manager.set_window_title('Amazon')
        plt.show()

    def alibaba_price_review_plot(self):
        global alibaba_df
        alibaba_df.sort_values(by=['product_price', 'review_count'])
        alibaba_df.plot(kind='scatter', x='product_price', y='review_count', color='blue')
        plt.legend(loc='best', fontsize=11)
        plt.xlabel('Review Count')
        plt.ylabel('Price')
        fig = pylab.gcf()
        fig.canvas.manager.set_window_title('Alibaba')
        plt.show()

    def price_plot_click(self):
        if len(amazon_df) == 0:
            messagebox.showinfo("No Data", "Searching products required first")
        elif len(alibaba_df) == 0:
            messagebox.showinfo("No Data", "Searching products required first")
        else:
            # self.amazon_price_review_plot()
            # self.alibaba_price_review_plot()
            amazon_df.sort_values(by=['product_price', 'review_count'])
            amazon_df.plot(kind='scatter', x='product_price', y='review_count', color='red')
            alibaba_df.sort_values(by=['product_price', 'review_count'])
            alibaba_df.plot(kind='scatter', x='product_price', y='review_count', color='blue')
            plt.legend(loc='best', fontsize=11)
            plt.xlabel('Price')
            plt.ylabel('Review Count')
            fig = pylab.gcf()
            fig.canvas.manager.set_window_title('Price/Review Scatter plot')
            plt.show()

    def get_product_entry(self):
        global e
        e = self.entry.get()
        if e == '':
            self.progress_label.configure(text="Cannot search for nothing")
            messagebox.showwarning("Empty Search Field", "Empty search field, please try again...")
        else:
            global product_list
            product_list = [e]
            self.progress_label.configure(text=f"Products to search: {e}")
            self.product_search_on_click()

    def display_baba_results(self):
        global selection
        selection = self.radio_var.get()
        order = self.combobox_1.get()
        display = self.show_var.get()
        if is_on:
            df = pd.DataFrame(columns=alibaba_headers)
            for index, row in alibaba_df.iterrows():
                flag = True
                product = row['item_searched'].lower()
                search_words = product.split(' ')
                title = row['product_title'].lower()
                for word in search_words:
                    if word in title:
                        pass
                    else:
                        flag = False
                        break
                if flag:
                    df.loc[len(df.index)] = row
        else:
            df = alibaba_df
        if len(df) == 0:
            messagebox.showinfo("No Alibaba Products", "No products matching results")
        else:
            if selection == 0 and order == "Lowest to Highest":
                df = alibaba_df.sort_values('product_price', ascending=True)
            elif selection == 1 and order == "Lowest to Highest":
                df = alibaba_df.sort_values('review_count', ascending=True)
            elif selection == 2 and order == "Lowest to Highest":
                df = alibaba_df.sort_values('product_rating', ascending=True)
            elif selection == 0 and order == "Highest to Lowest":
                df = alibaba_df.sort_values('product_price', ascending=False)
            elif selection == 1 and order == "Highest to Lowest":
                df = alibaba_df.sort_values('review_count', ascending=False)
            elif selection == 2 and order == "Highest to Lowest":
                df = alibaba_df.sort_values('product_rating', ascending=False)
            if display == 1:
                df = df.head(5)
            root = tk.Tk()
            root.title('Alibaba Product Search Results')
            root.geometry("1000x500")

            # Add Some Style
            style = ttk.Style()

            # Pick A Theme
            style.theme_use('default')

            # Configure the Treeview Colors
            style.configure("Treeview",
                            background="#D3D3D3",
                            foreground="black",
                            rowheight=25,
                            fieldbackground="#D3D3D3")

            # Change Selected Color
            style.map('Treeview',
                      background=[('selected', "#347083")])

            # Create a Treeview Frame
            tree_frame = tk.Frame(root)
            tree_frame.pack(pady=10)

            # Create a Treeview Scrollbar
            tree_scroll_y = tk.Scrollbar(tree_frame)
            tree_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
            tree_scroll_x = tk.Scrollbar(tree_frame, orient="horizontal")
            tree_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)

            # Create The Treeview
            my_tree = ttk.Treeview(tree_frame, yscrollcommand=tree_scroll_y.set, xscrollcommand=tree_scroll_x.set,
                                   selectmode="extended")
            my_tree.pack()

            # Configure the Scrollbar
            tree_scroll_y.config(command=my_tree.yview)
            tree_scroll_x.config(command=my_tree.xview)

            # Set up new treeview
            my_tree["column"] = list(df.columns)
            my_tree["show"] = "headings"
            # Loop thru column list for headers
            for column in my_tree["column"]:
                my_tree.heading(column, text=column)

            # Put data in treeview
            df_rows = df.to_numpy().tolist()
            for row in df_rows:
                my_tree.insert("", "end", values=row)

            # Pack the treeview finally
            my_tree.pack()

    def display_amazon_results(self):
        global selection
        selection = self.radio_var.get()
        order = self.combobox_1.get()
        display = self.show_var.get()
        if is_on:
            df = pd.DataFrame(columns=alibaba_headers)
            for index, row in amazon_df.iterrows():
                flag = True
                product = row['item_searched'].lower()
                search_words = product.split(' ')
                title = row['product_title'].lower()
                for word in search_words:
                    if word in title:
                        pass
                    else:
                        flag = False
                        break
                if flag:
                    df.loc[len(df.index)] = row
        else:
            df = amazon_df
        if len(df) == 0:
            messagebox.showinfo("No Amazon Products", "No products matching results")
        else:
            if selection == 0 and order == "Lowest to Highest":
                df = amazon_df.sort_values('product_price', ascending=True)
            elif selection == 1 and order == "Lowest to Highest":
                df = amazon_df.sort_values('review_count', ascending=True)
            elif selection == 2 and order == "Lowest to Highest":
                df = amazon_df.sort_values('product_rating', ascending=True)
            elif selection == 0 and order == "Highest to Lowest":
                df = amazon_df.sort_values('product_price', ascending=False)
            elif selection == 1 and order == "Highest to Lowest":
                df = amazon_df.sort_values('review_count', ascending=False)
            elif selection == 2 and order == "Highest to Lowest":
                df = amazon_df.sort_values('product_rating', ascending=False)
            if display == 1:
                df = df.head(5)
            root = tk.Tk()
            root.title('Amazon Product Search Results')
            root.geometry("1000x500")

            # Add Some Style
            style = ttk.Style()

            # Pick A Theme
            style.theme_use('default')

            # Configure the Treeview Colors
            style.configure("Treeview",
                            background="#D3D3D3",
                            foreground="black",
                            rowheight=25,
                            fieldbackground="#D3D3D3")

            # Change Selected Color
            style.map('Treeview',
                      background=[('selected', "#347083")])

            # Create a Treeview Frame
            tree_frame = tk.Frame(root)
            tree_frame.pack(pady=10)

            # Create a Treeview Scrollbar
            tree_scroll_y = tk.Scrollbar(tree_frame)
            tree_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
            tree_scroll_x = tk.Scrollbar(tree_frame, orient='horizontal')
            tree_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)

            # Create The Treeview
            my_tree = ttk.Treeview(tree_frame, yscrollcommand=tree_scroll_y.set, xscrollcommand=tree_scroll_x.set,
                                   selectmode="extended")
            my_tree.pack()

            # Configure the Scrollbar
            tree_scroll_y.config(command=my_tree.yview)
            tree_scroll_x.config(command=my_tree.xview)

            # Set up new treeview
            my_tree["column"] = list(df.columns)
            my_tree["show"] = "headings"
            # Loop thru column list for headers
            for column in my_tree["column"]:
                my_tree.heading(column, text=column)

            # Put data in treeview
            df_rows = df.to_numpy().tolist()
            for row in df_rows:
                my_tree.insert("", "end", values=row)

            # Pack the treeview finally
            my_tree.pack()

    def switch(self):
        global is_on
        if is_on:
            is_on = False
        else:
            is_on = True

    def clear_text(self):
        self.entry.delete(0, 'end')

    def button_event(self):
        self.label_info_1.configure(text='Hello')
        self.update()
        print("Button pressed")

    def export_to_db(self):
        if len(amazon_df) == 0:
            messagebox.showwarning("No Amazon Data", "No Amazon data to export")
        else:
            try:
                df_to_temp_amazon_table()
                self.progress_label.configure(text="Successfully exported data to temp tables")
            except ProgrammingError:
                if messagebox.askyesno("Tables Already Exist", "Would you like to delete temp tables?\n\n"
                                                                  "WARNING: Removing temp tables without reallocating"
                                                                  " data can result in permanent loss of data"):
                    delete_tables()
                    self.progress_label.configure(text="Successfully deleted temp tables, retry exporting data")
                else:
                    return
        if len(alibaba_df) == 0:
            messagebox.showwarning("No Alibaba Data", "No Alibaba data to export")
        else:
            try:
                df_to_temp_baba_table()
                self.progress_label.configure(text="Successfully exported data to temp tables")
            except ProgrammingError:
                if messagebox.askyesno("Tables Already Exist", "Would you like to delete temp tables?\n\n"
                                                               "WARNING: Removing temp tables without reallocating"
                                                               " data can result in permanent loss of data"):
                    delete_tables()
                    self.progress_label.configure(text="Successfully deleted temp tables, retry exporting data")
                else:
                    return

    def temp_to_main_tables(self):
        try:
            temp_to_main()
            self.progress_label.configure(text="Successfully moved data to main tables")
        except ProgrammingError:
            "ERROR: No temp tables"
            messagebox.showerror("ERROR", "You must export data to temp tables first")

    def remove_temp_tables(self):
        try:
            delete_tables()
            self.progress_label.configure(text="Successfully deleted temp tables")
        except ProgrammingError:
            messagebox.showinfo("No Tables to Delete", "Temp Tables do not exist")
            print("Tables do not exist")

    def dark_mode(self):
        self.change_appearance_mode('dark')
        self.progress_label.configure(text="Dark mode activated")

    def light_mode(self):
        self.change_appearance_mode('light')
        self.progress_label.configure(text="Light mode activated")

    def change_appearance_mode(self, new_appearance_mode):
        customtkinter.set_appearance_mode(new_appearance_mode)

    def restart(self):
        try:
            delete_tables()
        except ProgrammingError:
            print("Tables do not exist")
        self.destroy()
        os.startfile("main.pyw")

    def on_closing(self, event=0):
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.destroy()
