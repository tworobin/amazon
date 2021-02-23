from requests_html import HTMLSession
from datetime import datetime
import time
from Functions import clean_text, clean_price, get_data, post_data, Compare, calculate

Name = 'Amazon'
url = "https://www.amazon.com.au/s?k="
abs_url = "https://www.amazon.com.au"

# Choose between 0.01 to 0.99
filter_level = 0.5


def get_links(given_name: str, given_url: str):
    session = HTMLSession()

    inp_name = given_name.replace(' ', '+').lower()

    search_url = given_url + inp_name

    r = session.get(url=search_url)

    items = r.html.find(".sg-col-4-of-12.s-result-item.s-asin.sg-col-4-of-16.sg-col.sg-col-4-of-20")

    print(f'{len(items)} Data Found for: {given_name}')

    link_list = []

    for item in items:
        try:
            links = item.find('.a-link-normal.a-text-normal')[0].absolute_links
            link = list(links)[0]
            link_list.append(link)
        except AttributeError:
            print('Link not found \n')
            print(item.find('.a-link-normal.a-text-normal')[0].text)
        except Exception as e:
            print(e, end="Hello\n\n")

    return link_list


def scrap(given_name: str, given_url=url):
    """
    :param given_name:
    :param given_url:
    :return: List of Scraped data, Data error count and Keyword
    """
    links = get_links(given_name, given_url)

    if len(links) < 1:
        return []

    data_list = []
    n = 1
    for link in links:
        print(f'Getting data from link {n} of {len(links)}...')
        n += 1
        try:
            t1 = datetime.now()
            while True:
                try:
                    session = HTMLSession()
                    prd_data = session.get(link)
                    break
                except:
                    print('Error while getting data..\nRetrying in 2 seconds..')
                    time.sleep(2)
            try:
                title = clean_text(prd_data.html.find('#productTitle')[0].text)
            except IndexError:
                continue

            try:
                prd_price = clean_price(prd_data.html.find('#price_inside_buybox')[0].text)
            except Exception as e:
                # print(f'\n{e} price\n{title}\n\n')
                prd_price = '0'

            try:
                merchant = clean_text(prd_data.html.find('#sellerProfileTriggerId')[0].text)
            except Exception as e:
                # print(f'\n\n{e} marchant \n{title}\n\n')
                merchant = 'NA'

            timestamp = datetime.now()
            main = {
                'name': title,
                'price': prd_price,
                'timestamp': timestamp,
                'merchant': merchant,
                'url': abs_url,
                'time': (datetime.now() - t1).total_seconds()
            }
            data_list.append(main)
        except AttributeError:
            pass

    return data_list


if __name__ == '__main__':
    obj = Compare()
    while True:
        # input('Press ENTER key to start:')
        resp, name, price, seller, prd = get_data()
        if not resp:
            print("Data error..")
            continue
        data = scrap(name, url)
        if len(data) < 1:
            print(f'No data found for: {name}')
            continue
        filtered_data, time = obj.filter(name, data, filter_level)
        if len(filtered_data) < 1:
            # For testing replace it with break
            continue
        min_price, competion, comp_price = calculate(filtered_data, seller)
        post_data(filtered_data, min_price, competion, comp_price, time, abs_url, prd)

        # Comment the line below for api part
        # break
