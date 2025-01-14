# coding:utf-8

import os
from PySide6.QtCore import (QThread, Signal)
import subprocess
from .transcribe import secondsToHMS

class SplitAudioFileWithSpeakersWorker(QThread):
    # 定义一个信号，用于在处理完成后发送结果
    result_signal = Signal(str)
    current_task_signal = Signal(str)

    def __init__(self, segments_path_info_list:list, output_path, parent=None):
        super().__init__(parent)
        self.segments_path_info_list = segments_path_info_list
        self.output_path = output_path

        # 检查输出目录
        if output_path and not os.path.exists(self.output_path):
            os.makedirs(self.output_path)
        
    def creatCommandLine(self, start_time, end_time, fileName, output_path, speaker):

        output_fileName = self.getOutPutFileName(output_path, start_time, end_time, speaker)
        # print(output_fileName)
        commandLine = []
        commandLine.append("ffmpeg")
        commandLine.append("-i")
        commandLine.append(fileName)
        commandLine.append("-ss")
        commandLine.append(start_time)
        commandLine.append("-to")
        commandLine.append(end_time)
        commandLine.append(output_fileName)
        return commandLine
    
    def getOutPutFileName(self, output_path:str, start_time:str, end_time:str, speaker:str):
        fileName = ""
        if not(speaker is None) and speaker != "":
            fileName = os.path.join(output_path, f"{speaker}_{start_time.replace(':','_')}_{end_time.replace(':','_')}.wav")
        else:
            fileName = os.path.join(output_path, f"UnClassedSpeaker_{start_time.replace(':','_')}_{end_time.replace(':','_')}.wav")
        return fileName
    

    def run(self):
        self.is_running = True

        for result in self.segments_path_info_list:
            segments,path,info = result
            base_path,file = os.path.split(path)
            print(f"    current task: {file}")

            self.current_task_signal.emit(file)

            if not self.output_path:
                output_path = base_path
            else:
                output_path = self.output_path
            output_path = os.path.join(output_path, ".".join(file.split('.')[:-1]))

            # print(output_path)
            # 检查输出路径
            if not os.path.exists(output_path):
                os.makedirs(output_path)
            
            for segment in segments:
                # if not segment.speaker : continue
                
                start_time = secondsToHMS(segment.start)
                end_time = secondsToHMS(segment.end)
                speaker = segment.speaker

                commandLine = self.creatCommandLine(start_time.replace(',','.'),end_time.replace(',','.'),path,output_path,speaker)
                
                # print(commandLine)
                temp_process = subprocess.Popen(commandLine, shell=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding="utf-8", text=True,
                                                creationflags=subprocess.CREATE_NO_WINDOW)
                temp_process.wait()

        # 完成后发送结果信号
        result = "over"
        self.result_signal.emit(result)
        self.stop()

    def stop(self):
        self.is_running = False
        self.quit()