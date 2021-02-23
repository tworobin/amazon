from time import sleep
from datetime import datetime
from requests import get, post
from string import punctuation
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import CountVectorizer

get_url = "https://tcesffb3s8.execute-api.ap-south-1.amazonaws.com/dev/productscraping/getinput"
post_url = "https://tcesffb3s8.execute-api.ap-south-1.amazonaws.com/dev/sitestats"

res = {
    "responseCode": 200,
    "responseMessage": "get scraping data from rabbitmq successfully",
    "preferencePojo": {
        "productId": 16,
        "product_scrap": "Google Pixel 3 XL (4g lte)",
        "productURL": "https://www.amazon.com.au/",
        "price": 150,
        "userId": 1,
        "createdDate": "2021-02-19 05:50:04",
        "status": 0,
        "sku": "SM-G981UBLU",
        "seller": "Xtrem"
    }
}


def get_data():
    # For API
    while True:
        data_dict = get(get_url).json()
        if data_dict['responseCode'] == 200:
            break
        else:
            print('Data not available..')
            sleep(4)
    # For Manual
    # data_dict = res
    if data_dict['responseCode'] != 200:
        return False, False, False, False
    prd = data_dict['preferencePojo']
    name = prd['product_scrap']
    price = prd['price']
    seller = prd['seller']
    return True, name, price, seller, prd


def post_data(data_list, min_price, competion, comp_price, time, url, prd):
    response = None
    for data in data_list:
        sub = {
            "siteUrl": url,
            "productName": data['name'],
            "preferenceId": prd['userId'],
            "minPrice": min_price,
            "userPrice": prd['price'],
            "competitionPrice": comp_price,
            "seller": data['merchant'],
            "scrapId": prd['productId'],
            "processing_time": data['time'] + time,
            "competionName": competion
        }
        # For API
        while True:
            try:
                response = post(post_url, json=sub)
                if response.status_code == 200:
                    break
            except:
                print('Can\'t post data retrying in 3 seconds')
                sleep(3)
        # For Manual
        print(f"{sub['productName']}\n {sub['userPrice']}, {sub['minPrice']}, {sub['competitionPrice']}\n")

    return response


def calculate(data_list, seller):
    p_l = []
    comp = False
    for i in data_list:
        if i['price'] != '0':
            p_l.append(i['price'])
        if i['merchant'].lower() == seller.lower():
            comp = True
    min_price = min(p_l)
    if not comp:
        return min_price, 'None', 0
    comp1 = data_list[0]['merchant']
    comp_price = min_price
    if comp1 == seller:
        for i in data_list:
            if i['seller'] != seller:
                comp1 = i[seller]
                comp_price = i['price']
                return min_price, comp1, comp_price
    return min_price, comp1, comp_price


def clean_text(string: str):
    text = ''
    for char in string:
        if char not in punctuation.replace('()', '').replace('&', ''):
            text = text + char
    return text


def clean_price(string: str):
    price = ''
    acceptable = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '.']
    for char in string:
        if char in acceptable:
            price = price + char
    return price


def sort_price(data_list: list):
    price_list = [n['price'] for n in data_list]
    try:
        price_list.sort(reverse=False)
    except:
        pass
    data_sorted = []
    for price in price_list:
        for single_data in data_list:
            if single_data['price'] == price and single_data not in data_sorted:
                data_sorted.append(single_data)

    return data_sorted


class Compare:
    @staticmethod
    def clean_text(given_string: str):
        text = ''.join([word for word in given_string if word not in punctuation])
        text = text.lower()
        return text

    @staticmethod
    def cosine_sim_vectors(vec1, vec2):
        vec1 = vec1.reshape(1, -1)
        vec2 = vec2.reshape(1, -1)

        return cosine_similarity(vec1, vec2)[0][0]

    def filter(self, main_string: str, to_compare: list, given_filter: float):
        t1 = datetime.now()
        print(f'{len(to_compare)} Data Found', end=' ')
        words = []
        for i in to_compare:
            words.append(i['name'])

        words.append(main_string)
        cleaned = list(map(self.clean_text, words))
        vectorized = CountVectorizer().fit_transform(cleaned)
        vector = vectorized.toarray()
        original = vector[-1]
        products = vector[:-1]
        filtered = []
        n = 0
        for product in products:
            similarity = self.cosine_sim_vectors(product, original)
            if similarity >= given_filter:
                filtered.append(to_compare[n])
            n += 1
        ret_data = []
        for i in to_compare:
            for j in filtered:
                if i == j:
                    ret_data.append(i)
        print(f'{len(ret_data)} will be uploaded..')
        return sort_price(ret_data), (datetime.now() - t1).total_seconds() / len(to_compare)
