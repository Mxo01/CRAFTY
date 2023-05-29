import warnings
warnings.filterwarnings('ignore')

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import networkx as nx
import requests
import json
import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# --- Read transactions file ---
transactions = pd.read_csv('./Dataset/transactions.csv', names = ['timestamp', 'blockId', 'txId', 'isCoinbase', 'fee'])
transactions['timestamp'] = pd.to_datetime(transactions['timestamp'], unit = 's') # Convert UNIX timestamp to readable date

# --- Read inputs file ---
inputs = pd.read_csv('./Dataset/inputs.csv', names = ['txId', 'prevTxId', 'prevTxPos'])

# --- Read outputs file ---
outputs = pd.read_csv('./Dataset/outputs.csv', names = ['txId', 'position', 'addressId', 'amount', 'scriptType'])

# --- Read mapping file ---
mapping = pd.read_csv('./Dataset/mapping.csv', names = ['hash', 'addressId'])
mapping.set_index('addressId', inplace = True)

# --- ANALYSIS ---

# --- (1) Number of transactions per block ---

# Calculation ...
tx_distribution = transactions.groupby('blockId').size() # Number of transactions per block
cumulative_tx = np.cumsum(tx_distribution) # Cumulative sum of transactions

# Plotting ...

# Create a figure and axes for subplots
fig, ax = plt.subplots(2, 1, figsize = (8, 6), sharex = True)

# Plotting the transaction distribution
ax[0].plot(tx_distribution, color = 'tab:red', linestyle = 'dashed', linewidth = 1)
ax[0].set_title('Blocks distribution')
ax[0].set_ylabel('Number of transactions')

# Plotting the cumulative transaction distribution
ax[1].plot(cumulative_tx, color='tab:blue', linewidth=2)
ax[1].set_title('Cumulative Blocks distribution')
ax[1].set_xlabel('Block Id')
ax[1].set_ylabel('Cumulative number of transactions')

# Add gridlines
ax[0].grid(True)
ax[1].grid(True)

# Add a legend
ax[0].legend(['Transactions'], loc = 'upper right')
ax[1].legend(['Cumulative Transactions'], loc = 'upper right')

# Display the plot
plt.tight_layout() # Adjust the padding between and around subplots
plt.show()

# --- (2) Number of transactions per block on two months ---

# Calculation ...
two_months_list = pd.date_range(start = '2009-01-03', end = '2012-12-31', freq = '1M')
months_list = list()
jan_feb = list()
mar_apr = list()
may_jun = list()
jul_aug = list()
sep_oct = list()
nov_dec = list()

for i in range(len(two_months_list) - 1):
  two_months = transactions[transactions['timestamp'].between(two_months_list[i], two_months_list[i + 1])]

  monthly_tx_distribution = two_months.groupby('blockId').size()
  monthly_distribution_mean = monthly_tx_distribution.mean()

  if (two_months_list[i].month_name() == 'January'):
    jan_feb.append(monthly_distribution_mean)
  if (two_months_list[i].month_name() == 'March'):
    mar_apr.append(monthly_distribution_mean)
  if (two_months_list[i].month_name() == 'May'):
    may_jun.append(monthly_distribution_mean)
  if (two_months_list[i].month_name() == 'July'):
    jul_aug.append(monthly_distribution_mean)
  if (two_months_list[i].month_name() == 'September'):
    sep_oct.append(monthly_distribution_mean)
  if (two_months_list[i].month_name() == 'November'):
    nov_dec.append(monthly_distribution_mean)

# Plotting ...
x = np.array([1, 2, 3, 4])
width = 0.1

fig, ax = plt.subplots(1, 1, figsize = (6.5, 5))
ax.set_title('Blocks distribution by years')
bar1 = ax.bar(x - 2 * width, jan_feb, width, color = 'tab:blue')
bar2 = ax.bar(x - width, mar_apr, width, color = 'tab:green')
bar3 = ax.bar(x, may_jun, width, color = 'tab:olive')
bar4 = ax.bar(x + width, jul_aug, width, color = 'tab:brown')
bar5 = ax.bar(x + 2 * width, sep_oct, width, color = 'tab:orange')
bar6 = ax.bar(x + 3 * width, nov_dec, width, color = 'tab:red')
ax.set_xticks(x + width/2, [2009, 2010, 2011, 2012])
ax.set_xlabel("Years")
ax.set_ylabel("Blocks Distribution")
ax.legend(['Jan-Feb', 'Mar-Apr', 'May-Jun', 'Jul-Aug', 'Sep-Oct', 'Nov-Dec'])
plt.show()

# --- (3) Total UTXO ---

# Calculation ...
spent_outputs = inputs.merge(outputs, left_on = ['prevTxId','prevTxPos'], right_on = ['txId','position'])

total_amount = outputs.amount.sum() # Total amount is the sum of all outputs
total_spent = spent_outputs.amount.sum() # Total spent is the sum of all spent outputs
total_utxo = total_amount - total_spent # Total UTXO is the difference between the sum of all outputs and the sum of all spent outputs

print('Total UTXO:', total_utxo)

# Plotting ...
plt.title('Amount distribution')
plt.axis('equal')
plt.pie([total_amount, total_spent, total_utxo], autopct='%1.1f%%', labels = ['Total amount', 'Total spent', 'Total UTXO'], colors = ['tab:cyan', 'tab:blue', 'tab:red'], startangle = 90)
plt.show()

# --- (4) Time between creation of inputs and amount spent ---

# Calculation ...
created_tx = inputs.merge(transactions, left_on = 'prevTxId', right_on = 'txId').rename(columns = {'timestamp': 'Creation date'})[['prevTxId', 'prevTxPos', 'Creation date']] # Merge inputs and transactions to obtain the creation date of each input
spent_tx = inputs.merge(transactions, how = 'inner').rename(columns = {'timestamp': 'Spent date'})[['txId', 'prevTxId', 'prevTxPos', 'Spent date']] # Merge inputs and transactions to obtain the spent date of each input

time_between = spent_tx.merge(created_tx, how = 'inner', on = ['prevTxId', 'prevTxPos']) # Merge spent and created transactions
time_between['Days between'] = (time_between['Spent date'] - time_between['Creation date']).dt.days # Calculate difference between spent and created dates

# Some difference are negative, so remove them and update dataframes
negative_differences = time_between.loc[time_between['Days between'] < 0]
only_positive_dates_mask1 = ~transactions['txId'].isin(negative_differences['txId'])
transactions = transactions.loc[only_positive_dates_mask1]
time_between = time_between.loc[time_between['Days between'] >= 0]

# Group by days of difference
grouped_by_difference = time_between.groupby('Days between')['prevTxId'].size() # Group by days of difference and count the number of outputs
time_distribution = pd.DataFrame({'outputs': grouped_by_difference.values, 'days': grouped_by_difference.index}) # Create a dataframe with the number of outputs and the days of difference to plot a chart

# Plotting ...
plt.title('Time between creation of inputs and amount spent')
plt.xlabel('Days of difference')
plt.ylabel('Number of outputs')
plt.stackplot(time_distribution['days'], time_distribution['outputs'], color = 'tab:purple')
plt.yscale(value = 'log')
plt.show()

# --- (5) Personal analysis (Fee Distribution) ---

# Calculation ...
positive_fee_distribution = transactions.loc[transactions['fee'] > 0]
null_fee_distribution = transactions.loc[transactions['fee'] == 0]

# Plotting ...
explode = (0.1, 0)

plt.title('Fee distribution')
plt.axis('equal')
plt.pie([len(positive_fee_distribution), len(null_fee_distribution)], autopct='%1.1f%%', explode = explode, labels = ['Positive fee', 'Null fee'], shadow = True, startangle = 90)
plt.show()

# --- (5) Personal analysis (Fee Distribution through years) ---

# Calculation ...
grouped_by_positive_fee = positive_fee_distribution.groupby(positive_fee_distribution['timestamp'].dt.year).size() # Group transactions with positive fees by year
grouped_by_null_fee = null_fee_distribution.groupby(null_fee_distribution['timestamp'].dt.year).size() # Group transactions with null fees by year

# Plotting ...
plt.title('Fee distribution through years')
plt.xlabel('Years')
plt.ylabel('Fee distribution')
plt.xticks([2009, 2010, 2011, 2012])
plt.plot([], [], color = 'tab:red')
plt.plot([], [], color = 'tab:brown')
plt.stackplot([2009, 2010, 2011, 2012], grouped_by_positive_fee, grouped_by_null_fee, colors = ['tab:red', 'tab:brown'])
plt.legend(['Positive fee', 'Null fee'])
plt.show()

# --- (5) Personal analysis (Correlation between Amount and Fee) ---

# Calculation ...
outputs_tx = outputs.merge(transactions, on = 'txId') # Merge outputs and transactions to obtain the fee and the amount of each output

# Plotting ...

# Scatter plot to represent the correlation between Amount and Fee
plt.title('Correlation between Amount and Fee')
plt.xlabel('Amount')
plt.ylabel('Fee')
plt.scatter(outputs_tx['amount'], outputs_tx['fee'], color = 'tab:green')
plt.xscale(value = 'log')
plt.yscale(value = 'log')
plt.show()

# Heatmap to represent the correlation between some fields of the Dataset
seaborn_heatmap = sns.heatmap(outputs_tx[['txId', 'addressId', 'scriptType', 'blockId', 'isCoinbase']].corr(), annot = True, cmap = 'YlGnBu')
seaborn_heatmap.set_title('Correlation between some fields')
plt.show()

# --- CLUSTERING ---

transactions_graph = nx.DiGraph() # Create a directed graph

# Hash specific address
def hash(address):
  return mapping.loc[address]['hash'] # Get the hash of the address

inputs_tx = inputs.merge(transactions, how = 'inner')[['txId', 'prevTxId', 'prevTxPos']] # Merge inputs and transactions
grouped_by_inputs = inputs_tx.groupby('txId')['prevTxId'].size() # Group by txId and count the number of inputs

mask = list(map(lambda inp: (inp > 1), grouped_by_inputs.values)) # Map each value of grouped_by_inputs with a boolean value (True if the value is greater than 1, False otherwise)

more_than_one_tx = (inputs_tx.loc[inputs_tx['txId'].isin((grouped_by_inputs.loc[mask]).index)]).reset_index(drop = True) # Get the inputs with more than one txId

all_tx = more_than_one_tx.merge(outputs, left_on = ['prevTxId', 'prevTxPos'], right_on = ['txId', 'position']).rename(columns = {'txId_x': 'txId'})[['txId', 'addressId']] # Merge the previous dataframe with outputs to obtain the addressId of each input

transactions_addresses = all_tx.groupby('txId')['addressId'].apply(list).to_dict() # Create a dictionary with txId as key and a list of addresses as value

# --- Clustering Algorithm ---

# Step 1
transactions_graph.add_nodes_from(mapping.index) # Add all nodes (addresses) to the graph

# Step 2
# For each address list in transactions_addresses
for addresses in transactions_addresses.values():
  head = addresses[0] # Get the first address of the list
  # For each address in the list
  for address in addresses[1:]:
    # If the address is not the head and the edge hasn't been added yet to the graph (to avoid duplicates or self-loops)
    if not(transactions_graph.has_edge(head, address)) and (address != head):
      transactions_graph.add_edge(head, address) # Add the edge to the graph

# Step 3
generator = nx.weakly_connected_components(transactions_graph) # Get the connected components of the graph

clusters = list(generator) # Get the connected components
clusters_len = list(map(lambda c : len(c), clusters)) # Map each components with its length (cluster)

sorted_clusters = sorted(clusters, key = len, reverse = True) # Get a copy of the connected components sorted by length (disceding order)
sorted_clusters_len = sorted(clusters_len, reverse = True) # Map each components with its length (cluster) ordered by length (descending order)

top10_clusters = sorted_clusters[:10] # Get the top 10 clusters
hashed_top10_clusters = list(map(lambda cluster : list(map(lambda address : hash(address), cluster)), top10_clusters)) # Map each address of each cluster with its hash
top10_clusters_len = sorted_clusters_len[:10] # Get the top 10 clusters length
print('Top 10 clusters size:', top10_clusters_len)
print('Number of clusters:', len(clusters))

max_cluster = top10_clusters_len[0] # Get the max cluster
print('Max cluster size:', max_cluster)
min_cluster = sorted_clusters_len[-1:][0] # Get the min cluster
print('Min cluster size:', min_cluster)
mean_clustering = np.mean(sorted_clusters_len) # Get the mean clustering
print('Mean clustering size:', mean_clustering)

# Plotting ...
plt.title('Clusters size distribution')
plt.xlabel('Clusters')
plt.ylabel('Number of addresses')
plt.plot(clusters_len, color = 'tab:green')
plt.yscale(value = 'log')
plt.show()

# --- WEB SCRAPING ---

# --- Wallet Explorer ---
wallet_explorer_url = 'https://www.walletexplorer.com/'

wallets_WE = {} # Dictionary to store the couple (cluster, wallet name)
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 ' + ' (KHTML, like Gecko) Chrome/61.0.3163.100Safari/537.36'}

# Extract the wallet name from the raw text (implemented if exists a spaced wallet name)
def extract_wallet_name(wallet_string):
  wallet_name = ''

  # For each character in the string (starting from the 7th character)
  for i in range(7, len(wallet_string), 1):
    if wallet_string[i] == '(': # If the character is '(' break the loop
      break
    wallet_name += wallet_string[i] # Add the character to the wallet name

  return wallet_name[:-1]

# Try to deanonymize addresses and get the wallet name
def deanonymize_addresses_WE(url, cluster, c_index, wallets):
  current_cluster = 'Cluster ' + str(c_index) # Get the current cluster
  wallet_name_found = False # Boolean to check if the wallet name has been found
  wallet_name = '' # Initialize the wallet name
  max_tries = 0 # Max number of tries to get the wallet name (starting from 0 and limited to 15)

  # For each hashed address
  for address in cluster:
    # If the max number of tries has been reached
    if max_tries == 15:
      break # Break the loop

    r = requests.get(url, {'q': address}, headers = headers) # Try to reach the page

    # If the status code is 429 (Too many requests)
    if r.status_code == 429:
      print('Too many requests, try again later')
      break

    html = r.text # Get the html page

    soup = BeautifulSoup(html, 'html.parser') # Parse the html using BeautifulSoup

    # Get the wallet name
    wallet_title = soup.find('h2') # Find the first h2 tag (it contains the wallet name)

    # If the wallet tag is not None
    if wallet_title is not None:
      wallet_name = extract_wallet_name(wallet_title.text) # Get the wallet name
      # Check if the wallet name is not inside "[]" (deanonymized correctly)
      if not wallet_name.startswith('['): 
        wallets[current_cluster] = wallet_name # Add the couple (cluster, wallet name) to the wallets dictionary
        wallet_name_found = True # Set the boolean to True
        break # Break the loop (every address of the cluster has the same wallet name)

    max_tries += 1 # Increment the max number of tries
    time.sleep(5) # Wait 5 seconds before the next request

  if not wallet_name_found:
    wallet_name = 'Unknown wallet name'
    wallets[current_cluster] = wallet_name # The wallet name is unknown
  
  # Append the couple (cluster, wallet name) to the json file
  data = json.loads(json.dumps(wallets)) # Load the current object
  data.update({current_cluster: wallet_name}) # Add the couple (cluster, wallet name)

  # Overwrite the json file with the updated object
  with open('wallets_WE.json', 'w') as f:
    f.write(json.dumps(data, indent = 2))
  
for index in range(len(hashed_top10_clusters)):
  deanonymize_addresses_WE(wallet_explorer_url, hashed_top10_clusters[index], index + 1, wallets_WE)

# --- BitInfoCharts ---
bitcoin_info_charts_url = 'https://bitinfocharts.com/'

driver = webdriver.Chrome() # Create a new Chrome web driver to cominicate with the browser

wallets_BIC = {} # Dictionary to store the couple (cluster, wallet name)

def deanonymize_addresses_BIC(url, cluster, c_index, wallets):
  current_cluster = 'Cluster ' + str(c_index) # Get the current cluster
  wallet_name_found = False # Boolean to check if the wallet name has been found
  wallet_name = '' # Initialize the wallet name
  max_tries = 0 # Max number of tries to get the wallet name (starting from 0 and limited to 15)

  # For each hashed address
  for address in cluster:
    # If the max number of tries has been reached
    if max_tries == 15:
      break # Break the loop

    driver.get(url + 'bitcoin/address/' + address) # Get the url of the address

    try:
      # Wait until the wallet name is loaded and get it via XPath
      wallet_name = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '/html/body/div[3]/div[3]/table/tbody/tr/td/table/tbody/tr[1]/td[2]/small/a'))).text.split(': ')[1] # Get the wallet name

      # If the wallet tag is not None
      if wallet_name is not None:
        # Check if the wallet name is not a number (deanonymized correctly)
        if not wallet_name.isdigit(): 
          wallets[current_cluster] = wallet_name # Add the couple (cluster, wallet name) to the wallets dictionary
          wallet_name_found = True # Set the boolean to True
          break # Break the loop (every address of the cluster has the same wallet name)
    except:
      print(f'TimeoutException, the wallet name has not been loaded to the html for the address {address}')
    
    max_tries += 1 # Increment the max number of tries
    time.sleep(5) # Wait 5 seconds before the next request

  if not wallet_name_found:
    wallet_name = 'Unknown wallet name'
    wallets[current_cluster] = wallet_name # The wallet name is unknown

  # Append the couple (cluster, wallet name) to the json file
  data = json.loads(json.dumps(wallets)) # Load the current object
  data.update({current_cluster: wallet_name}) # Add the couple (cluster, wallet name)

  # Overwrite the json file with the updated object
  with open('wallets_BIC.json', 'w') as f:
    f.write(json.dumps(data, indent = 2))

for index in range(len(hashed_top10_clusters)):
  deanonymize_addresses_BIC(bitcoin_info_charts_url, hashed_top10_clusters[index], index + 1, wallets_BIC)