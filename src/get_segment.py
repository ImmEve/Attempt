import csv
import json
import os
import re
import subprocess
import requests
from bs4 import BeautifulSoup


class Reference():
    def __init__(self, Reference_Type, Reference_Size, Subsegment_Duration, Starts_with_SAP, SAP_Type):
        self.Reference_Type = Reference_Type
        self.Reference_Size = Reference_Size
        self.Subsegment_Duration = Subsegment_Duration
        self.Starts_with_SAP = Starts_with_SAP
        self.SAP_Type = SAP_Type


class Track():
    def __init__(self, Track_Time, Track_Number, Track_Position):
        self.Track_Time = Track_Time
        self.Track_Number = Track_Number
        self.Track_Position = Track_Position


class Box():
    def __init__(self, itag, start, end, video_name, datapath):
        self.itag = itag
        self.start = start
        self.end = end
        mp4_itag = [160, 133, 134, 135, 136, 137, 298, 299, 394, 395, 396, 397, 398, 399, 400, 401, 571, 694, 695, 696,
                    697, 698, 699, 700, 701, 702]
        webm_itag = [278, 242, 243, 244, 247, 248, 271, 313, 302, 303, 308, 315, 272, 330, 331, 332, 333, 334, 335, 336,
                     337]
        if self.itag in mp4_itag:
            self.itag_type = 'mp4'
            self.get_metedata_mp4(video_name, datapath)
        elif self.itag in webm_itag:
            self.itag_type = 'webm'
            self.get_metedata_webm(video_name, datapath)
        else:
            raise ValueError('Itag Wrong')

    def get_metedata_mp4(self, video_name, datapath):
        videopath = datapath + '/download/{}/{}_{}.mp4'.format(video_name, video_name, self.itag)
        with open(videopath, 'rb') as f:
            header_data = f.read(10000)
        sidx = header_data[self.start:self.end + 1]

        self.Box_Siz = int.from_bytes(sidx[:4], byteorder='big')
        sidx = sidx[4:]
        self.Box_Type = int.from_bytes(sidx[:4], byteorder='big')
        sidx = sidx[4:]
        self.Version = int.from_bytes(sidx[:1], byteorder='big')
        sidx = sidx[1:]
        self.Flags = int.from_bytes(sidx[:3], byteorder='big')
        sidx = sidx[3:]
        self.Reference_ID = int.from_bytes(sidx[:4], byteorder='big')
        sidx = sidx[4:]
        self.Timescale = int.from_bytes(sidx[:4], byteorder='big')
        sidx = sidx[4:]
        if self.Version == 0:
            self.Earliest_Presentation_Time = int.from_bytes(sidx[:4], byteorder='big')
            sidx = sidx[4:]
            self.First_Offset = int.from_bytes(sidx[:4], byteorder='big')
            sidx = sidx[4:]
        elif self.Version == 1:
            self.Earliest_Presentation_Time = int.from_bytes(sidx[:8], byteorder='big')
            sidx = sidx[8:]
            self.First_Offset = int.from_bytes(sidx[:8], byteorder='big')
            sidx = sidx[8:]
        else:
            raise Exception('Version Inexistence')
        self.Reserved = int.from_bytes(sidx[:2], byteorder='big')
        sidx = sidx[2:]
        self.Reference_Count = int.from_bytes(sidx[:2], byteorder='big')
        sidx = sidx[2:]

        self.reference = []
        self.reference_list = []
        while len(sidx) != 0:
            Reference_Type = int.from_bytes(sidx[:1], byteorder='big')
            sidx = sidx[1:]
            Reference_Size = int.from_bytes(sidx[:3], byteorder='big')
            sidx = sidx[3:]
            Subsegment_Duration = int.from_bytes(sidx[:4], byteorder='big')
            sidx = sidx[4:]
            Starts_with_SAP = int.from_bytes(sidx[:1], byteorder='big')
            sidx = sidx[1:]
            SAP_Type = int.from_bytes(sidx[:3], byteorder='big')
            sidx = sidx[3:]

            ref = Reference(Reference_Type, Reference_Size, Subsegment_Duration, Starts_with_SAP, SAP_Type)
            self.reference.append(ref)
            self.reference_list.append(Reference_Size)

    def get_metedata_webm(self, video_name, datapath):
        videopath = datapath + '/download/{}/{}_{}.webm'.format(video_name, video_name, self.itag)
        with open(videopath, 'rb') as f:
            header_data = f.read(10000)
        cues = header_data[self.start:self.end + 1]

        self.Cues_Header = int.from_bytes(cues[:6], byteorder='big')
        cues = cues[6:]

        self.track = []
        self.track_list = []
        while len(cues) != 0:
            Track_Time_Flag = int.from_bytes(cues[3:4], byteorder='big')
            cues = cues[4:]
            Track_Time_Length = Track_Time_Flag - 0x80
            Track_Time = int.from_bytes(cues[:Track_Time_Length], byteorder='big')
            cues = cues[Track_Time_Length:]
            Track_Number_Flag = int.from_bytes(cues[3:4], byteorder='big')
            cues = cues[4:]
            Track_Number_Length = Track_Number_Flag - 0x80
            Track_Number = int.from_bytes(cues[:Track_Number_Length], byteorder='big')
            cues = cues[Track_Number_Length:]
            Track_Position_Flag = int.from_bytes(cues[1:2], byteorder='big')
            cues = cues[2:]
            Track_Position_Length = Track_Position_Flag - 0x80
            Track_Position = int.from_bytes(cues[:Track_Position_Length], byteorder='big')
            cues = cues[Track_Position_Length:]

            tra = Track(Track_Time, Track_Number, Track_Position)
            self.track.append(tra)
            if len(self.track) > 1:
                self.track_list.append(self.track[-1].Track_Position - self.track[-2].Track_Position)


class Video():
    def __init__(self, url, datapath, fingerpath):
        self.url = url
        self.video_name = self.url.split('=')[1]
        self.mp4_itag = [160, 133, 134, 135, 136, 137, 298, 299, 394, 395, 396, 397, 398, 399, 400, 401, 571, 694, 695,
                         696, 697, 698, 699, 700, 701, 702]
        self.webm_itag = [278, 242, 243, 244, 247, 248, 271, 313, 302, 303, 308, 315, 272, 330, 331, 332, 333, 334, 335,
                          336, 337]
        self.get_itag_list()
        # self.download_video(datapath)
        # self.get_websource(datapath)
        self.analyse_websource(datapath)
        self.analyse_video(fingerpath, datapath)

    def get_itag_list(self):
        command = 'yt-dlp -F ' + self.url
        itag_output = subprocess.run(command, stdout=subprocess.PIPE, text=True, encoding='utf-8')
        itag_output = itag_output.stdout.split('\n')
        self.itag_list = []
        for line in itag_output:
            if 'video only' in line:
                if int(line.split(' ')[0]) in (self.mp4_itag + self.webm_itag):
                    self.itag_list.append(int(line.split(' ')[0]))

    def download_video(self, datapath):
        if not os.path.exists(datapath + '/download/' + self.video_name):
            os.makedirs(datapath + '/download/' + self.video_name)
        for itag in self.itag_list:
            if itag in self.mp4_itag:
                videopath = datapath + '/download/{}/{}_{}.mp4'.format(self.video_name, self.video_name, itag)
            elif itag in self.webm_itag:
                videopath = datapath + '/download/{}/{}_{}.webm'.format(self.video_name, self.video_name, itag)
            else:
                raise ValueError('Itag Wrong')
            command = 'yt-dlp -f {} {} -o {}'.format(itag, self.url, videopath)
            subprocess.run(command, shell=True, capture_output=True, text=True)

    def get_websource(self, datapath):
        response = requests.get(self.url)
        if response.status_code == 200:
            with open(datapath + '/websource/' + self.video_name + '.html', 'w', encoding='utf-8') as f:
                f.write(response.text)

    def analyse_websource(self, datapath):
        with open(datapath + '/websource/' + self.video_name + '.html', 'r', encoding='utf-8') as f:
            html_content = f.read()
        soup = BeautifulSoup(html_content, 'html.parser')
        # 找到所有的 <script> 标签
        script_tags = soup.find_all('script')
        # 定义正则表达式来匹配 JavaScript 变量
        pattern = re.compile(r'var\s+ytInitialPlayerResponse\s*=\s*({.*?});', re.DOTALL)

        # 在每个 <script> 标签中搜索匹配的内容
        for script_tag in script_tags:
            # 获取 <script> 标签的所有内容，并将其合并为一个字符串
            script_content = ''.join(map(str, script_tag.contents))
            # 使用正则表达式匹配 JavaScript 变量
            match = pattern.search(script_content)
            if match:
                # 提取匹配的 JavaScript 变量内容
                javascript_code = match.group(1)
        data = json.loads(javascript_code)
        service_tracking_params = data.get('streamingData', {}).get('adaptiveFormats', [])

        self.itag_indexrange = {}
        for param in service_tracking_params:
            itag = param.get('itag')
            indexRange = param.get('indexRange')
            indexRange['start'] = int(indexRange['start'])
            indexRange['end'] = int(indexRange['end'])
            self.itag_indexrange[itag] = indexRange

    def analyse_video(self, fingerpath, datapath):
        self.itag_box = {}
        for itag in self.itag_list:
            if itag not in [247, 302]:
                continue
            start, end = self.itag_indexrange[itag]['start'], self.itag_indexrange[itag]['end']
            try:
                box = Box(itag, start, end, self.video_name, datapath)
            except:
                box = None
            self.itag_box[itag] = box

            if box is not None:
                with open(fingerpath, 'a') as f:
                    url = 'https://www.youtube.com//watch?v=' + self.video_name
                    f.write(url + ',' + str(itag) + ',' + box.itag_type + ',')
                    if box.itag_type == 'mp4':
                        seg_list = box.reference_list
                    elif box.itag_type == 'webm':
                        seg_list = box.track_list
                    f.write(str(self.itag_indexrange[itag]['start']) + ',' + str(self.itag_indexrange[itag]['end']) + ',')
                    f.write(str(len(seg_list)) + ',')
                    seg_str = ''
                    for seg in seg_list:
                        seg_str = seg_str + '/' + str(seg)
                    f.write(seg_str + ',')

                    segsum_list = [sum(seg_list[:i + 1]) + self.itag_indexrange[itag]['end'] for i in range(len(seg_list))]
                    segsum_str = ''
                    for segsum in segsum_list:
                        segsum_str = segsum_str + '/' + str(segsum)
                    f.write(segsum_str)
                    f.write('\n')


if __name__ == '__main__':
    # download = Video('https://www.youtube.com//watch?v=9JvjLI_WJTo')

    datapath = 'E:/project/Attempt/data/record'
    fingerpath = 'E:/project/Attempt/data/fingerprint/segment.csv'

    with open('E:/project/Attempt/data/temp/url_list.csv', 'r') as f:
        reader = csv.reader(f)
        txt = list(reader)
    url_list = [i[0] for i in txt]

    video_list = []
    for url in url_list:
        video = Video(url, datapath, fingerpath)
        video_list.append(video)
