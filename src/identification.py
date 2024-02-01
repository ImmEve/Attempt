import csv
from markov_alg import *
import time
import pickle


class Database_Finger():
    def __init__(self, url, itag, type, indexRange, seg_list):
        self.url = url
        self.itag = itag
        self.type = type
        self.indexRange = indexRange
        self.seg_list = seg_list
        self.generate_list = []

    def generate_chunk(self, alpha):
        chunk_list = []
        flag_list = []
        chunk = 0
        flag = 0
        for seg in self.seg_list:
            if chunk + seg > 2 * 1024 * 1024 or flag == alpha:
                chunk_list.append(chunk)
                flag_list.append(flag)
                chunk = 0
                flag = 0
            chunk = chunk + seg
            flag = flag + 1
        chunk_list.append(chunk)
        flag_list.append(flag)
        self.generate_list.append([chunk_list, flag_list])


class Gateway_Finger():
    def __init__(self, url, seg_list):
        self.url = url
        self.seg_list = seg_list


def getdata(datapath):
    with open(datapath + '/segment.csv', 'r') as f:
        reader = csv.reader(f)
        data = list(reader)
    database = []
    for line in data:
        indexRange = {'start': int(line[3]), 'end': int(line[4])}
        seg_list = line[6].split('/')[1:]
        seg_list = [int(i) for i in seg_list]
        database_finger = Database_Finger(line[0], int(line[1]), line[2], indexRange, seg_list)
        database.append(database_finger)

    with open(datapath + '/gateway.csv', 'r') as f:
        reader = csv.reader(f)
        data = list(reader)
    gateway = []
    for line in data:
        seg_list = line[2].split('/')[:-1]
        seg_list = [int(i) for i in seg_list]
        gateway_finger = Gateway_Finger(line[0], seg_list)
        gateway.append(gateway_finger)
    return database, gateway


if __name__ == '__main__':
    database, gateway = getdata('E:/project/Attempt/data/fingerprint')
    result = []

    db2, db3, db4 = [], [], []
    for finger in database:
        for i in range(2, 5):
            finger.generate_chunk(i)

    for finger in database:
        db2.append({'url': finger.url, 'finger': finger.generate_list[0][0]})
        db3.append({'url': finger.url, 'finger': finger.generate_list[1][0]})
        db4.append({'url': finger.url, 'finger': finger.generate_list[2][0]})

    offline_audio_thd = 600 * 1024
    high_orders, high_bins_count, high_win_size = 5, 160, 21
    low_orders, low_bins_count, low_win_size = 1, 160, 14
    # offline_data = db2
    for offline_data in [db2, db3, db4]:
        count = 0
        for gateway_finger in gateway:
            gateway_url = gateway_finger.url
            gateway_chunk = gateway_finger.seg_list
            markov_alg = Markov_alg(gateway_chunk, offline_data, offline_audio_thd, high_orders, high_bins_count,
                                    high_win_size, low_orders, low_bins_count, low_win_size)
            if markov_alg.pred_stream != -1:
                if gateway_url == markov_alg.pred_stream.video_url:
                    count = count + 1
        print(count / len(gateway))
        result.append(count / len(gateway))

    t = time.strftime('%m_%d_%H_%M', time.localtime(time.time()))
    with open('E:/project/Attempt/data/result/result_' + t + '.data', 'wb') as f:
        pickle.dump(result, f)
