import json
import random
import time
import requests
from bs4 import BeautifulSoup

def create_par_row(category: str, location: str) -> str:
    """Create link parameters string with user parameters

    Args:
        category (str): yelp.com category
        location (str): any location

    Returns:
        str: parameters in url format 
    """
    
    replace_elems = {
        " ": "+",
        ",": "%2C"
    }
    par_row = "find_desc={0}s&find_loc={1}".format(category,location)
    for k,v in replace_elems.items():
        par_row = par_row.replace(k,v)
    
    return par_row

def find_max_len(parameters_row: str) -> int:
    """find max page number

    Args:
        parameters_row (str): searching parameters in url format

    Returns:
        int: number of max page
    """
    
    r = requests.get("https://www.yelp.com/search?" + parameters_row)
    soup = BeautifulSoup(r.text,'html.parser')
    
    #find pages counter element
    divs = soup.find("div",{"class","css-1aq64zd"})
    children = divs.findChild("span")
    
    #extruct max number
    max_pages = children.string.split()[-1]
    
    return int(max_pages)

def find_reviews(url: str) -> list:
    """find first five reviwes 

    Args:
        url (str): business yelp.com url

    Returns:
        list: list with first five rewies information: {"name": ,"location": ,"date": }
    """
    
    r = requests.get(url)
    soup = BeautifulSoup(r.text,"html.parser")
    
    #find first five reviwes
    comments = soup.find_all("li",{"class":"css-1q2nwpv"})[:5]
    
    reviewers = []
    
    #extruct name,location and date from review information
    for comment in comments:
        review = {}
        try:
            review["name"] = comment.find("a",{"class": "css-19v1rkv"}).string
        except:
            review["name"] = None
        
        try:
            review["location"] = comment.find("span",{"class": "css-qgunke"}).string
        except:
            review["location"] = None
            
        try:
            review["date"] = comment.find("span",{"class": "css-chan6m"}).string
        except:
            review["date"] = None

        reviewers.append(review)
            
    return reviewers

def find_xhr_info(parameters_row: str) -> list:
    """find businesses information on page using xhr request

    Args:
        parameters_row (str): searching parameters in url format

    Returns:
        list: businesses information from current page
    """
    
    url = "https://www.yelp.com/search/snippet?" + parameters_row
    r = requests.get(url)
    
    page_buisnesses = []
    
    for el in r.json()["searchPageProps"]["mainContentComponentsListProps"]: 
        business = {}
        
        if "bizId" in el: #find elements with business information
            
            business["name"] = el["searchResultBusiness"]["name"]
            business["rating"] = el["searchResultBusiness"]["rating"]
            business["reviews"] = el["searchResultBusiness"]["reviewCount"]
            business["url"] = "https://www.yelp.com" + el["searchResultBusiness"]["businessUrl"]
            
            try:
                business["website"] = el["searchResultBusiness"]["website"]["href"]
            except:
                business["website"] = None
            
            page_buisnesses.append(business)
    
    return page_buisnesses

def crawl_main(category: str, location: str,*, business_limit: int = 99999, pages_limit: int = 99999) -> list:
    """retrieve information about companies found based on user parameters

    Args:
        category (str): yelp.com category
        location (str): any location
        business_limit (int, optional): number of max returned businesses. Defaults to 99999.
        pages_limit (int, optional): number of max processed pages (1 page - 10 businesses). Defaults to 99999.

    Returns:
        list: businesses information in current category and location
    """
    
    #create row for url with user parameters
    parameters_row = create_par_row(category,location)
    
    #find max page number
    max_pages = find_max_len(parameters_row)
    
    
    start = 0 #variable to list pages and control limits
    businesses_list_result = []
    
    while start < max_pages*10 and start < business_limit and start < pages_limit*10:
        
        page_businesses = find_xhr_info(parameters_row + f"&start={start}")[:business_limit-start]
        businesses_list_result.extend(page_businesses)
        
        start += 10
        
        #pause to avoid server overload 
        timeout = random.uniform(0.5,1)
        time.sleep(timeout)
    
    for ind, bs in enumerate(businesses_list_result):
        businesses_list_result[ind]["reviews"] = find_reviews(bs["url"])
        
        timeout = random.uniform(0.5,1)
        time.sleep(timeout)
        
    return businesses_list_result


if __name__ == "__main__":
    data = crawl_main("Contractors","San Francisco, CA",pages_limit= 3)
    with open("result.json","w") as file:
        json.dump(data,file,indent=4,ensure_ascii=False)