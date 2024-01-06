# -*- coding: utf-8 -*-
import datetime
import os
import re
import sys
import webbrowser
import PySide6 
from PySide6.QtWidgets import QMainWindow, QApplication,QTableWidgetItem, QFileDialog, QMessageBox, QHeaderView  
from PySide6.QtCore import QMimeData, Qt
from PySide6.QtGui import QIcon  
import xlrd
import sqlite3  
import zipfile
import py7zr
from Ui import Ui_MainWindow  
import everything64
import yaml



def searchAllDisk():
    everything64.search()

def searchAuto(file_info_list,Key=""):
    if len(file_info_list)==0:
        return 
    if Key=="":
        latest_non_shortcut = None  
        for path, timestamp, size in file_info_list:  
            filename = os.path.basename(path)
            if not filename.lower().endswith(('.lnk', '.ink')):  
                if latest_non_shortcut is None or timestamp > latest_non_shortcut[1]:  
                    latest_non_shortcut = (path, timestamp, size)  
        if latest_non_shortcut:#可能全是快捷方式
            return latest_non_shortcut
        else:
            return 
    else :
        # 过滤出非快捷方式文件  
        non_shortcut_files = [(filename, time, size) for filename, time, size in file_info_list if not filename.lower().endswith(('.lnk', '.ink'))]  
        strings_to_check=Key.split(",")
        # 找出包含所有字符串的最新文件  
        latest_file = None  
        latest_time = datetime.datetime.min  
        for path, time, size in non_shortcut_files:  
            filename = os.path.basename(path)
            if all(string in filename for string in strings_to_check) and time > latest_time:  
                latest_file = (path, time, size)  
                latest_time = time  
        if latest_file:
            return latest_file
        else:
            return 

def saveZipFile(List,rule=None,zipPath=""):#作用打包zip
    zip_file = zipfile.ZipFile(zipPath, 'w', zipfile.ZIP_DEFLATED) 
    for i in List:
        id,name,Path,submit=i
        if submit == 1:
            if rule is None:
                filename = os.path.basename(Path) 
            else:
                filename = rule.replace('-id-',str(id)).replace('-name-',str(name)).replace('---',str("-"))+os.path.splitext(Path)[-1]
            zip_file.write(Path, filename)
    zip_file.close() 



def save7zFile(List,rulu="",zipPath=""):  
    with py7zr.SevenZipFile(zipPath, mode='w') as z:  
        for i in List:
            id,name,Path,submit=i
            if submit == 1:
                if rulu is None:
                    filename = os.path.basename(Path) 
                else:
                    filename = rulu.replace('-id-',str(id)).replace('-name-',str(name)).replace('---',str("-"))+os.path.splitext(Path)[-1]
                z.write(Path, filename)  

class Config:  
    def __init__(self, filename="./config.yaml"):  
        self.filename = filename  
        self.data = self.load()  
        self.AutoInit()

    def load(self):  
        try:  
            with open(self.filename, 'r') as file:  
                return yaml.safe_load(file)  
        except FileNotFoundError:  
            return {}  
  
    def save(self):  
        with open(self.filename, 'w') as file:  
            yaml.safe_dump(self.data, file)  
  
    def query_by_name(self, name):  
        return self.data.get(name)  
  
    def update_by_name(self, name, value):  
        if name in self.data:  
            self.data[name] = value  
            self.save()  
            return True  
        else:  
            return False
    def update_if_not_exists(self, name, value):  
        if name not in self.data:  
            self.data[name] = value  
            self.save()  
            return True  
        else:  
            return False
    def AutoInit(self):
        self.update_if_not_exists("openpath","./data.db")#存储着上一次打开数据的地址



class DB():
    def __init__(self,filepath="data.db"):
        self.conn = sqlite3.connect(filepath)  
        self.cursor = self.conn.cursor()  
        self.cursor.execute('''  
        CREATE TABLE IF NOT EXISTS my_table (  
            id INTEGER PRIMARY KEY,  
            name TEXT,  
            quotePath TEXT,  
            submit BOOLEAN
        )  
        ''')  
        self.conn.commit()   
        #self.conn.close()
    def open(self,filepath="data.db"):
        self.close()
        self.conn = sqlite3.connect(filepath)  
        self.cursor = self.conn.cursor()  
        self.cursor.execute('''  
        CREATE TABLE IF NOT EXISTS my_table (  
            id INTEGER PRIMARY KEY,  
            name TEXT,  
            quotePath TEXT,  
            submit BOOLEAN
        )  
        ''')  
        self.conn.commit()   
    def saveAsAndOpen(self,fname):
        List=self.getAllData()
        self.close()
        self.conn = sqlite3.connect(fname)  
        self.cursor = self.conn.cursor()
        self.cursor.execute('''  
        CREATE TABLE IF NOT EXISTS my_table (  
            id INTEGER PRIMARY KEY,  
            name TEXT,  
            quotePath TEXT,  
            submit BOOLEAN
        )  
        ''')  
        self.conn.commit()  
        for i in List:
            id, name,path,submit=i
            self.cursor.execute("INSERT INTO my_table (id, name, quotePath,submit) VALUES (?,?,?,?)", (id, name,path,submit))  
        window.printInfo()
    def getSubmitAndAllCount(self):
        self.cursor.execute("SELECT COUNT(*) FROM my_table WHERE submit = 1")  
        submit_count, = self.cursor.fetchone()
        self.cursor.execute("SELECT COUNT(*) FROM my_table")  
        row_count,=self.cursor.fetchone()
        return (row_count, submit_count)
    def addRosterDict(self,id,name):
        self.cursor.execute("SELECT * FROM my_table WHERE id=?", (id,)) 
        result = self.cursor.fetchone()  
        if result:  
            return   
        else:  
            self.cursor.execute("INSERT INTO my_table (id, name) VALUES (?, ?)", (id, name)) 
        self.conn.commit() 
        window.printInfo()
    def getAllData(self):
        self.cursor.execute("SELECT * FROM my_table") 
        data_list = [row for row in self.cursor]  
        #print(data_list)
        return data_list
    
    def updata(self,id, quotePath, submit):
        if id != None:
            self.cursor.execute("UPDATE my_table SET quotePath = ?, submit = ? WHERE id = ?", (quotePath, submit, id))  
            self.conn.commit() 
            window.printLine("导入成功，学号为"+str(id)) 
        else:
            window.printLine("导入失败，请检查学号是否正确or总名单内有没有这个学号or不满足关键字") 
        window.printInfo()
        
    def updataSub(self,id,name, submit):
        self.cursor.execute("UPDATE my_table SET submit = ? WHERE id = ?", (submit, id))  
        self.conn.commit() 
        if submit ==False:
            window.printLine("关闭学号 "+str(id)+" "+name+"的提交") 
        else:
            window.printLine("开启学号 "+str(id)+" "+name+"的提交")
        window.printInfo()
    def getSubmitPathList(self):
        self.cursor.execute("SELECT quotePath FROM my_table WHERE submit = true")  
        quote_paths = [row[0] for row in self.cursor.fetchall()]  
        return quote_paths
    def getNoSubmitIdList(self):
        self.cursor.execute("SELECT id FROM my_table WHERE submit=0 OR submit IS NULL;")  
        idList = [row[0] for row in self.cursor.fetchall()]  
        return idList
    
    def commit(self):
        self.conn.commit()
    def close(self):
        self.conn.commit()   
        self.conn.close()




class Data():
    #每位学生使用学号作为唯一标识.
    def __init__(self):
        pass


    def UseTxtGetList(self,path):#从Txt获取映射关系
        if path == "":
            return
        try:
            for line in open(path,encoding='utf-8'): 
                str=line.replace("\n", "")
                str1=str.replace(" ", "")
                if len(str1)!=0:
                    list = str.split(" ")
                    id =int(list[0])
                    db.addRosterDict(id,list[1])
                    db.commit()
                    #print(self.rosterDict)
        except Exception as e:
            return e
            
    def UseExcelGetList(self,path):
        if path == "":
            return
        try:
            data = xlrd.open_workbook(path)
            table = data.sheets()[0]
            row = table.nrows
            for i in range(row):
                id = int(table.cell(i,0).value)
                db.addRosterDict(id,table.cell(i,1).value)
                db.commit()
        except Exception as e:
            return e
        
    
    def analysisNameGetID(self,path,key=""):#识别功能。传入路径，判断是哪位同学提交的作业（学号）,key为关键字。不包含关键字的均会被移除。
        #解析拖入的文件路径来判断。
        fileName = os.path.basename(path)
        data_list=db.getAllData()
        self.idList = []
        for i in data_list:
            self.idList.append(i[0])
        count = -1
        if key == "":
            for i in self.idList:
                count += 1
                if str(i) in fileName:
                    return self.idList[count]
        else:
            keyList=key.split(',')
            for i in self.idList:
                count += 1
                if str(i) in fileName:
                    for j in keyList:
                        if j in fileName:
                            return self.idList[count]
    def analysisName(self,path,key=""):
        id = self.analysisNameGetID(path,key)
        if id == -1 and id is None:
            return -1 #表示没有搜索到。
        else :
            db.updata(id,path,True)
        
        


class MainWindow(QMainWindow, Ui_MainWindow):  
    def __init__(self):  
        super().__init__()  
        self.setupUi(self)
        self.Connect()
        self.setAcceptDrops(True)
        self.Table.setAcceptDrops(True)#设置表格支持文件拖入
        self.tabletShow()
        self.updataTable()
        self.printLine("多功能文件打包器by AliceSohii")

    def Connect(self):
        self.GetToTxt.triggered.connect(self.ClickedGetToTxt)
        self.GetToExcel.triggered.connect(self.ClickerGetToExcel)
        self.ToZip.triggered.connect(self.saveZip)
        self.To7z.triggered.connect(self.save7z)
        self.UseKeySelect.clicked.connect(self.useKeySearchAllDisk)
        self.To7z.triggered.connect(self.save7z)
        self.StartDB.triggered.connect(self.Start)
        self.OpenDB.triggered.connect(self.Open)
        self.SaveAsDB.triggered.connect(self.SaveAs)
        self.Help.triggered.connect(self.pdfHelp)

    def ClickedGetToTxt(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "选择文件","","Text Files (*.txt);;All Files (*)")
        err=data.UseTxtGetList(file_path)
        self.updataTable()
        if err:
            QMessageBox.critical(None, "警告 txt格式错误", "每行应该按学号空格姓名排序")
    def ClickerGetToExcel(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "选择文件","","xls (*.xls);xlsx (*.xlsx)")
        err=data.UseExcelGetList(file_path)
        self.updataTable()
        if err:
            QMessageBox.critical(None, "警告 内容格式错误 or 中文路径", "第一张表的AB列分别填入学号和姓名")
    
    def dragEnterEvent(self, event):  
        if event.mimeData().hasUrls():  
            event.accept()  
        else:  
            event.ignore()  
    def dropEvent(self, event):  #拖入文件进行识别
        if event.mimeData().hasUrls():  
            event.setDropAction(Qt.CopyAction)  
            event.accept()  
            UseKey = self.UseKeyMod.isChecked()
            Key = self.UseKeyInput.text()
            NoKey = self.UseKeyInput.text()=="" or not UseKey
            for url in event.mimeData().urls():  
                path = url.toLocalFile()  
                count = -1
                if NoKey:
                    count = data.analysisName(path)
                if UseKey:
                    count = data.analysisName(path,Key)
                if count != -1:
                    self.updataTable()
        else:  
            event.ignore()
    def tabletShow(self):
        self.Table.setColumnCount(4)  # 设置列数
        self.header = self.Table.horizontalHeader()  
        self.header.setSectionResizeMode(QHeaderView.ResizeToContents)
        self.Table.setHorizontalHeaderLabels(['学号', '姓名', '文件路径','是否提交'])
        self.Table.cellClicked.connect(self.onCellClicked)  # 连接单元格点击事件  
    def updataTable(self):
        self.Table.setRowCount(len(db.getAllData()))  # 设置行数
        Data=db.getAllData()
        DataLen=len(Data)
        for i in range(DataLen):
            self.Table.setRowHeight(i, 14) 
        for i, row in enumerate(Data):  
            for j, value in enumerate(row): 
                if j ==3 and value ==1:
                    value = "√"
                if j ==3 and value ==0:
                    value = "x"
                item = QTableWidgetItem(str(value if value is not None else ""))  
                if value =="√":
                    item.setTextAlignment(Qt.AlignRight)
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.Table.setItem(i, j, item)
        self.printInfo()
        
        
    def onCellClicked(self, row, column):  
        if column == 3:
            row_value = self.Table.item(row, column).text()
            id =int(self.Table.item(row, 0).text())
            name=self.Table.item(row, 1).text()
            if row_value == "":
                return
            elif row_value == "√":
                item = QTableWidgetItem("x")
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.Table.setItem(row, column, item)
                db.updataSub(id,name,False)
            elif row_value == "x":
                item = QTableWidgetItem("√")
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                item.setTextAlignment(Qt.AlignRight)
                self.Table.setItem(row, column, item)
                db.updataSub(id,name,True)
                
    def saveZip(self):  
        fname = QFileDialog.getSaveFileName(self, '导出zip', '', 'zip (*.zip)')  
        if fname[0]:  
            try:
                saveZipFile(db.getAllData(),self.RenameLineEdit.text(),fname[0])
            except:
                QMessageBox.critical(None, "警告 导出错误", "检测是否有文件读写权限限制")
    
                  
    def save7z(self):  
        fname = QFileDialog.getSaveFileName(self, '导出7z', '', '7z (*.7z)')  
        if fname[0]:
            try:
                save7zFile(db.getAllData(),self.RenameLineEdit.text(),fname[0])
            except:
                QMessageBox.critical(None, "警告 导出错误", "检测是否有文件读写权限限制")
    def useKeySearchAllDisk(self):
        reply = QMessageBox.question(None, "即将进行全盘搜索", "将通过搜索关键字(如果打开的话)和学号自动匹配未提交的文件\n时间靠前优先。人数过多请先保存。\n(强烈建议和同学们约定提交作业时给文件附加关键字)\n（已经提交的不会进行搜索）", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            print("User selected Yes.")
            idList = db.getNoSubmitIdList()
            UseKey = self.UseKeyMod.isChecked()
            Key = self.UseKeyInput.text()
            NoKey = self.UseKeyInput.text()=="" or not UseKey 
            if NoKey:
                for i in idList:
                    searchIdList = everything64.search(str(i))
                    max_tuple=searchAuto(searchIdList)
                    if max_tuple:
                        db.updata(i,max_tuple[0].replace("\\","/"),True)
            if UseKey:
                for i in idList:
                    searchIdList = everything64.search(str(i))
                    max_tuple=searchAuto(searchIdList,Key)
                    if max_tuple:
                        db.updata(i,max_tuple[0].replace("\\","/"),True)
        self.updataTable()
    def Start(self):
        fname = QFileDialog.getSaveFileName(self, '新建数据库', '', 'db (*.db)')  
        if fname[0]:
            try:
                db.open(fname[0])
                config.update_by_name("openpath", fname[0])
                self.updataTable()
            except:
                QMessageBox.critical(None, "警告 导出错误", "检测是否有文件读写权限限制")
    def Open(self):
        fname = QFileDialog.getOpenFileName(self, '打开数据库', '', 'db (*.db)')  
        if fname[0]:
            try:
                db.open(fname[0])
                config.update_by_name("openpath", fname[0])
                self.updataTable()
            except:
                QMessageBox.critical(None, "警告 导出错误", "检测是否有文件读写权限限制")
        pass
    def SaveAs(self):
        fname = QFileDialog.getSaveFileName(self, '新建数据库', '', 'db (*.db)')  
        if fname[0]:
            try:
                db.saveAsAndOpen(fname[0])
                config.update_by_name("openpath", fname[0])
                self.updataTable()
            except:
                QMessageBox.critical(None, "警告 导出错误", "检测是否有文件读写权限限制")
    def printInfo(self,info=""):
        allcount,submit=db.getSubmitAndAllCount()
        self.Info.setText("人数 "+str(allcount)+" 提交 "+str(submit)+" 剩余 "+str(allcount-submit)+"  "+info)
    def printLine(self,info):
        self.printL.setText(info)
    def pdfHelp(self):
        webbrowser.open_new(os.getcwd()+"./Assets/help.pdf")
        
def MainWindowName(Title="多功能文件打包器by AliceSohii"):
    window.setWindowTitle(Title)
    

if __name__ == "__main__": 
    
    config=Config() 
    data=Data()
    db=DB(config.query_by_name("openpath"))
    app = QApplication(sys.argv)  
    window = MainWindow()  
    MainWindowName()
    icon = QIcon("./Assets/icon.png")
    app.setWindowIcon(icon)
    window.show()  
    
    sys.exit(app.exec_())
    