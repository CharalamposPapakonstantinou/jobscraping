from selenium import webdriver
import time
import pandas as pd
import os
import numpy as np
import re
from tqdm import tqdm
import pyshorteners

#Import Selenium Packages
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys

import sys
import subprocess
if 'darwin' in sys.platform:
    print('Running \'caffeinate\' on MacOSX to prevent the system from sleeping')
    subprocess.Popen('caffeinate')

try:
    driver.quit()
except:
    print('Already Closed')

# driver = webdriver.Chrome()
driver = webdriver.Safari(executable_path='/usr/bin/safaridriver')
driver.implicitly_wait(10)
driver.maximize_window()
shortener = pyshorteners.Shortener()

# Change position, location
position_raw = ["data analyst","aocs engineer","gnc engineer"]
location_raw = ["austria","france","denmark","netherlands","spain","luxembourg","switzerland","sweden"]
keywords=['aerospace','python','matlab','sql','sql server','remote','remotely','work from home'] # NOT case sensitive
only_remote=1
n_jobs_to_see=100 # how many jobs to see in each specific L,P pair


result_pd = pd.DataFrame()

# L=0
for L in range(0,len(location_raw)):
    for P in range(0, len(position_raw)):

        print(position_raw[P]+' '+location_raw[L])

        position = position_raw[P].replace(' ', "%20")
        location = location_raw[L].replace(' ', "%20")

        url1='https://www.linkedin.com/jobs/search/?currentJobId=2662929045&keywords='+position+'&location='+location+'&position=1&pageNum=0'
        if (only_remote==1): url1=url1+'&f_WT=2'


        driver.get(url1)
        # wait = WebDriverWait(driver, 6)  # wait up to 6 seconds
        # wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(6)


        try:
            # find # of jobs
            yraw=driver.find_element(By.CLASS_NAME,"results-context-header__job-count").get_attribute("innerText")
            y1=yraw.replace(',','')
            y2=y1.replace('+','')
            n=pd.to_numeric(y2)
            print('# of jobs found: ',y1)


            # close banner the first time
            if L==0 and P==0:
                send = driver.find_element(By.XPATH,"//button[@action-type='DENY']")
                driver.execute_script("arguments[0].click();", send)



            # saturate the number of job to see (n_jobs_to_see) in the max available jobs
            if n_jobs_to_see>n: n_jobs_to_see=n

            start = time.time()
            dates  = driver.find_elements(By.CLASS_NAME,"job-search-card__listdate")
            while len(dates)<=n_jobs_to_see:
                dates = driver.find_elements(By.CLASS_NAME, "job-search-card__listdate")
                try:
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(0.5)
                    btn = driver.find_element(By.XPATH, "//button[@aria-label='See more jobs']")
                    driver.execute_script("arguments[0].click();", btn)
                    time.sleep(0.5)
                except:
                    break
            end = time.time()
            print(end - start)
            time.sleep(1)



            companyname= []
            titlename= []
            urllist = []
            numappl_list=[]
            dates_list=[]
            seniority_list=[]
            maintxt_not_loaded_list=[]


            companies = driver.find_elements(By.XPATH,"//*[@class='base-search-card__subtitle']")
            titles = driver.find_elements(By.XPATH,"//*[@class='base-search-card__title']")
            urls   = driver.find_elements(By.CLASS_NAME,"base-card__full-link")
            dates  = driver.find_elements(By.CLASS_NAME,"job-search-card__listdate")

            min_rows=min([len(urls),len(dates),len(titles),len(companies)])
            print(min_rows)



            keywords_col = [[] for i in range(len(keywords))]


            for i in tqdm(range(min_rows)):

                companyname.append(companies[i].get_attribute("innerText"))

                titlename.append(titles[i].get_attribute("innerText"))

                urllist.append(urls[i].get_attribute("href"))
                if len(urllist[i])>= 255: urllist[i] = shortener.tinyurl.short(urllist[i]) #shorten long urls

                dates_list.append(dates[i].get_attribute('innerText'))

                # Change job-page
                driver.execute_script("arguments[0].click();", urls[i])
                time.sleep(3)


                numappl  = driver.find_element(By.CLASS_NAME,"num-applicants__caption").get_attribute('innerText')
                numappl_numbers_only = int(re.sub('[^0-9]', '', numappl))
                print(numappl_numbers_only)
                numappl_list.append(numappl_numbers_only)

                seniority  = driver.find_elements(By.CLASS_NAME,"description__job-criteria-text--criteria")[0].get_attribute('innerText')
                seniority=re.sub(' +', ' ', seniority).strip(' \n')
                print(seniority)
                seniority_list.append(seniority)


                maintxt = driver.find_element(By.CLASS_NAME, "details-pane__content").get_attribute('innerText')
                fulltxt=titlename[i]+' '+maintxt

                for j in range(0,len(keywords)):
                    if keywords[j].lower() in fulltxt.lower():
                        keywords_col[j].append('1')
                    else:
                        keywords_col[j].append('0')


                if maintxt=='':
                    maintxt_not_loaded_list.append('1')
                else:
                    maintxt_not_loaded_list.append('0')




            colnames=['Job Title', 'Company Name','Location_Raw','Position_Raw','URL','Appl_Num','Date Posted','Seniority']+keywords+['Main Not Loaded']
            array=np.array([titlename,companyname,[location_raw[L]]*len(titlename),[position_raw[P]]*len(titlename),urllist,numappl_list,dates_list,seniority_list,*keywords_col,maintxt_not_loaded_list]).T
            p=pd.DataFrame(array,columns=colnames)

            result_pd = pd.concat([result_pd, p])
            print(result_pd)


            time.sleep(2)

        except:
            print('No jobs found')


driver.quit()


# Save to excel
result_pd.to_excel('/Users/charalamposp/Desktop/Job Search Remote='+str(only_remote)+'.xlsx', index=False)





##################################################################


# use this if i want to connect before the search
# if i use this, i have to
# remove the webdriver.Safari(executable_path='/usr/bin/safaridriver') inside th for loop

# driver = webdriver.Safari(executable_path='/usr/bin/safaridriver')
# driver.implicitly_wait(10)
# driver.maximize_window()
#
# driver.get('https://linkedin.com/')
# time.sleep(1)
#
# username = driver.find_element(By.XPATH,'//*[@id="session_key"]')
# password = driver.find_element(By.XPATH,'//*[@id="session_password"]')
#
# username_input = input('What is your LinkedIn username/mail?')
# username.send_keys(username_input)
# pass_input = input('What is your LinkedIn password?')
# password.send_keys(pass_input)
#
# login_btn = driver.find_element(By.XPATH,"//button[@class='sign-in-form__submit-button']")
# time.sleep(1)
# driver.execute_script("arguments[0].click();", login_btn)

##
