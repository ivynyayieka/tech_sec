from flask import Flask, request, render_template
app = Flask(__name__)

import pandas as pd
from datetime import datetime


#import the file from the web
import requests
from bs4 import BeautifulSoup
import pandas as pd
from unicodedata import normalize
import re
from datetime import datetime
from pandas import read_csv 
from sklearn.feature_extraction.text import CountVectorizer
import json
from flatten_json import flatten


# I can give a number or use None to remove maximum ceiling & display all columns
pd.options.display.max_columns = None

# # I want to be able to see the entire narrative, so remove the maximum width for each column
# pd.options.display.max_colwidth = None

# pd.options.display.float_format = '{:,.0f}'.format

import string

# for playwright stuff
import time
from playwright.async_api import async_playwright
import asyncio
import nest_asyncio




# this is final

# one_title_searchable="Apple Inc"

@app.route('/')
def index():
    return render_template('index.html')



@app.route('/search', methods=['POST'])
def search():
    one_title_searchable = request.form.get('one_title_searchable')
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    info = loop.run_until_complete(extracting_stock_compensation_for_one_company())
    if info is None:
        return "No information found", 404
    return info



async def extracting_stock_compensation_for_one_company():

    # Get the one_title_searchable from the user
    one_title_searchable = request.form.get('one_title_searchable')
    async def getting_10_k_link(one_title_searchable):
        #### ON THE SEC HOME PAGE
        # going to sec page
        sec_home_playwright = await async_playwright().start()
        sec_home_browser = await sec_home_playwright.chromium.launch(headless = False)
        sec_home_page = await sec_home_browser.new_page()

        await sec_home_page.goto("https://www.sec.gov/edgar/searchedgar/companysearch")
        time.sleep(6)

        try:

            # input company name (here is where we can enter title variable from df from csv)

            await sec_home_page.fill("xpath=/html/body/div[1]/div/div/div/div[3]/div/div[2]/div[2]/div/div/article/div/div/div[1]/div[2]/div/div/div/div[1]/form/div[2]/input", one_title_searchable)
            time.sleep(6)

            # click search

            await sec_home_page.click("xpath=/html/body/div[1]/div/div/div/div[3]/div/div[2]/div[2]/div/div/article/div/div/div[1]/div[2]/div/div/div/div[1]/form/div[2]/button")
            time.sleep(6)

            #============
            # ON THE NEW PAGE RESULTING WITH ALL COMPANY DOCS
            #input 10K for search
            await sec_home_page.fill("xpath=/html/body/div[4]/div[2]/form/table/tbody/tr[3]/td[1]/input", "10-K")
            time.sleep(6)

            # click search

            await sec_home_page.click("xpath=/html/body/div[4]/div[2]/form/table/tbody/tr[3]/td[5]/input[1]")
            time.sleep(6)


            #get all 10K entries
            list_of_all_ten_k_entries_response= await sec_home_page.content()

            list_of_all_ten_k_entries_doc = BeautifulSoup(list_of_all_ten_k_entries_response, 'html.parser')

            #get the first 10K
            list_of_all_ten_k_entries_table = list_of_all_ten_k_entries_doc.find('table', class_='tableFile2')

            ten_k_entries_rows = list_of_all_ten_k_entries_table.find_all('tr')  # get the first row because it has the most recent 10K

            most_recent_ten_k_link = None

            for one_ten_k_entries_row in ten_k_entries_rows:
                one_ten_k_entries_row_cells = one_ten_k_entries_row.find_all('td')  # Assuming each cell is represented by a <td> tag
            #     print(one_ten_k_entries_row_cells)

                for one_ten_k_entries_row_cell in one_ten_k_entries_row_cells:
            #         print(one_ten_k_entries_row_cell)
                    if one_ten_k_entries_row_cell.text.strip() == '10-K':
                        ten_k_document_link_href = one_ten_k_entries_row_cell.find_next('td').find('a')['href']

                        ten_k_document_link_base = "https://www.sec.gov/"
                        ten_k_document_link_tail = ten_k_document_link_href
                        ten_k_document_link = ten_k_document_link_base + ten_k_document_link_tail

            #             print(document_link)

                        # Store the first 10-K link and break out of the loop
                        most_recent_ten_k_link = ten_k_document_link
                        break

                if most_recent_ten_k_link is not None:
                    break


            # ONCE I HAVE THE TEN K DOC LINK 
            # 3. Now on the page with the document and graphics table

            ten_k_doc_link_playwright = await async_playwright().start()
            ten_k_doc_link_browser = await ten_k_doc_link_playwright.chromium.launch(headless = False)
            ten_k_doc_link_page = await ten_k_doc_link_browser.new_page()

            time.sleep(6)

            await ten_k_doc_link_page.goto(most_recent_ten_k_link)
            time.sleep(6)



            # Initiate the html and beautiful soup content 

            list_of_doc_and_graphics_response= await ten_k_doc_link_page.content()

            list_of_doc_and_graphics_soup_doc = BeautifulSoup(list_of_doc_and_graphics_response, 'html.parser')

            # get actual_full_ten_k_document_link
            list_of_doc_and_graphics_table = list_of_doc_and_graphics_soup_doc.find('table', class_='tableFile')


            list_of_doc_and_graphics_rows = list_of_doc_and_graphics_table.find_all('tr')  # Assuming each row is represented by a <tr> tag

            for list_of_doc_and_graphics_row in list_of_doc_and_graphics_rows:
                list_of_doc_and_graphics_cells = list_of_doc_and_graphics_row.find_all('td')  # Assuming each cell is represented by a <td> tag
            #     print(cells)
                for list_of_doc_and_graphics_cell in list_of_doc_and_graphics_cells:
                    if list_of_doc_and_graphics_cell.text.strip() == '10-K':
                        actual_document_link = list_of_doc_and_graphics_cell.find_next('td').find('a')
                        if actual_document_link is not None:
                            actual_ten_k_document_href = actual_document_link['href']
            #                 print("Documents href:", document_href)
                            actual_ten_k_document_link_base="https://www.sec.gov/"
                            actual_ten_k_document_link_tail=actual_ten_k_document_href
                            actual_full_ten_k_document_link=actual_ten_k_document_link_base+actual_ten_k_document_link_tail
#                             global x
                            x=actual_full_ten_k_document_link
                            print(actual_full_ten_k_document_link)
                            print("#########")

                            


        except:
            pass

        finally:
            # Close the page and browser
            await ten_k_doc_link_page.close()
            await ten_k_doc_link_browser.close()
            await ten_k_doc_link_playwright.stop()

            # Close the sec_home page and browser
            await sec_home_page.close()
            await sec_home_browser.close()
            await sec_home_playwright.stop()
            return actual_full_ten_k_document_link
    
    
    
    x = await getting_10_k_link(one_title_searchable)
    
    
    
    
    
    
    # with change for link


    list_of_actual_full_ten_k_document_links = ["https://www.sec.gov/ix?doc=/Archives/edgar/data/789019/000156459022026876/msft-10k_20220630.htm"]

    actual_list_of_actual_full_ten_k_document_links = ["https://www.sec.gov//ix?doc=/Archives/edgar/data/320193/000032019322000108/aapl-20220924.htm","https://www.sec.gov/ix?doc=/Archives/edgar/data/789019/000156459022026876/msft-10k_20220630.htm","https://www.sec.gov/ix?doc=/Archives/edgar/data/1652044/000165204423000016/goog-20221231.htm"]

    async def get_actual_full_ten_k_document_content(x):
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(headless=False)
    #     browser = await playwright.firefox.launch(headless=False)

        page = await browser.new_page()

        await page.goto(x)
        time.sleep(10)

        while True:
            # Get the number of spans on the page
            spans_assigned = await page.query_selector_all("span")
            test = len(spans_assigned)

            # Scroll in increments of 5000 pixels
            await page.evaluate('''() => {
                let distance = 5000;
                window.scrollBy(0, distance);
            }''')
    #         await asyncio.sleep(3)

            time.sleep(10)


            spans_assigned_two = await page.query_selector_all("span")
            test2 = len(spans_assigned_two)
            if test == test2:
                break

        # Get the content of the page
        actual_full_ten_k_document_content = await page.content()
        time.sleep(10)

        await browser.close()
        time.sleep(10)
        await page.close()  # Add this line to close the page
        time.sleep(10)

        return actual_full_ten_k_document_content


    async def process_actual_full_ten_k_document(actual_full_ten_k_document_content):
        actual_full_ten_k_document_soup = BeautifulSoup(actual_full_ten_k_document_content, 'html.parser')
        return actual_full_ten_k_document_soup


    async def main():
        dict_titles=['actual_full_ten_k_document_link_collection',
                     'table_length',
                     'list_of_stock_based_values',
                     'first_stock_based_compensation',
                     'second_stock_based_compensation',
                     'third_stock_based_compensation']

        possible_titles = ['CONSOLIDATED STATEMENTS OF CASH FLOWS',
                           'CASH FLOWS STATEMENTS',
                           'Consolidated Statements of Cash Flows',
                           'Consolidated Statement of Cash Flows',
                          'CONSOLIDATED STATEMENT OF CASH FLOWS',
                          'STATEMENTS OF CONSOLIDATED CASH FLOWS',
                          'Consolidated Cash Flow Statement',
                          'Consolidated Statement of Cash Flow for the Years Ended December 31',
                          'STATEMENT OF CASH FLOWS',
                          'CONSOLIDATED STATEMENTS OF CASH FLOW',
                          'Statements of Consolidated Cash Flows']

        stock_related_texts = [
            'Stock-based compensation expense',
            'Stock-based compensation expense',
            'Share-based compensation expense',
            'Stock-based compensation',
            'Share-based compensation'
        ]

        all_ten_k_document_lists = []


    #     list_of_example_actual_full_ten_k_document_soup_doc = []

        # Define the group size
        group_size = 2
        items=[x]

        # Iterate over groups of items
        for start_index in range(0, len(items), group_size):
            group_items = items[start_index:start_index + group_size]

            list_of_example_actual_full_ten_k_document_soup_doc = []


    #         # Iterate over items within the group
    #         for item in group_items:
    #             print(item)

    #         # Add a separator for each group
    #         print("Group separator")




            url_to_parsed_content = {}


            for actual_full_ten_k_document_link in group_items:
                try:
                    actual_full_ten_k_document_link_collection = actual_full_ten_k_document_link
                    print(actual_full_ten_k_document_link)

                    for _ in range(3):
                        try:
                            actual_full_ten_k_document_content = await get_actual_full_ten_k_document_content(actual_full_ten_k_document_link)
                            example_actual_full_ten_k_document_soup_doc = await process_actual_full_ten_k_document(actual_full_ten_k_document_content)
                            list_of_example_actual_full_ten_k_document_soup_doc.append(example_actual_full_ten_k_document_soup_doc)
                                # Store the parsed content in the dictionary.
                            url_to_parsed_content[actual_full_ten_k_document_link] = example_actual_full_ten_k_document_soup_doc

                            break  # Break the loop if successful
                        except Exception as e:
                            print(f"An error occurred: {str(e)}. Retrying...")
                            time.sleep(15)
                except:
                    pass

            for actual_full_ten_k_document_link, one_actual_full_ten_k_document_soup_doc in url_to_parsed_content.items():
                ten_k_detail_list=[]

                if one_actual_full_ten_k_document_soup_doc:

                    elements = one_actual_full_ten_k_document_soup_doc.find_all(text=possible_titles)

                    if not elements:
                        print("Titles not found in the HTML.")
                        continue

                    for element in elements:
                        if element.strip() in possible_titles:
                            following_elements = element.find_all_next()
                            table = None

                            # Iterate through following elements and stop when a table is found or after three components
                            component_count = 0
                            for next_element in following_elements:
                                if next_element.name == 'table' and any(text in next_element.get_text() for text in stock_related_texts):
                                    table = next_element
                                    break
                                elif next_element.name in ['p', 'span']:
                                    component_count += 1
                                    if component_count >= 5:
                                        break

                            if table is None:
                                tables = one_actual_full_ten_k_document_soup_doc.find_all("table")
                                for t in tables:     
                                    if t:
                                        table_text = t.get_text()
                                        if any(title in table_text for title in possible_titles) and any(stock_related_text in table_text for stock_related_text in stock_related_texts):
                                            rows = t.find_all('tr')
                                            table_length = len(rows)
                                            print(f"Table Length from within: {len(rows)}") 
                                        break

                            if table:
                                rows = table.find_all('tr')
                                table_length=len(rows)

                                print(f"Table Length: {len(rows)}")                        

                                break



                    else:
                        print("No table found within or after the possible titles in the HTML.")

                else:
                    print("Document not processed, skipping")


                if table:
                    target_td = table.find('td', text=stock_related_texts)
                else:
                    target_td = None

                if target_td:
                    # Move up to the <tr> containing the <td> with "share-based compensation"
                    target_tr = target_td.find_parent('tr')

                    # Extract all the <td> values from the <tr> and put them in a column
                    values_in_column = [td.get_text(strip=True) for td in target_tr.find_all('td')]

                    # Output the values in the column
                    if values_in_column:
                        stock_stock_based_compensation_title=values_in_column[0]
                        list_of_stock_based_values=values_in_column
                        numbers_only_values_in_column = [entry for entry in values_in_column if any(char.isdigit() for char in entry)]
                        first_stock_based_compensation=numbers_only_values_in_column[0]
                        second_stock_based_compensation=numbers_only_values_in_column[1]
                        third_stock_based_compensation=numbers_only_values_in_column[2]
                        for value in values_in_column:
                            print(value)

                    ten_k_detail_list.append(actual_full_ten_k_document_link)
                    ten_k_detail_list.append(table_length)
                    ten_k_detail_list.append(list_of_stock_based_values)
                    ten_k_detail_list.append(first_stock_based_compensation)
                    ten_k_detail_list.append(second_stock_based_compensation)
                    ten_k_detail_list.append(third_stock_based_compensation)

                    first_rep = dict(zip(dict_titles, ten_k_detail_list))
                    all_ten_k_document_lists.append(first_rep)



                else:
                    print("The 'Share-Based Compensation' row not found!")
                time.sleep(10)

        # print(all_ten_k_document_lists)
        return all_ten_k_document_lists


    # Run the main coroutine
    nest_asyncio.apply()

    # Use asyncio.run() to run the main coroutine
    all_ten_k_document_lists_of_dicts=asyncio.run(main())

    print(all_ten_k_document_lists_of_dicts)
    
    return all_ten_k_document_lists_of_dicts






if __name__ == '__main__':
    app.run(debug=True)




