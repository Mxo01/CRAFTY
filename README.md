# **C**lustering and sc**RA**ping **F**or bi**T**coin deanon**Y**mization (CRAFTY)


**CRAFTY** is a University project that revolves around highly relevant topics such as *Web Scraping*, *Data Analysis*, and *Data Mining*. The project works with a Dataset comprising **Bitcoin** transactions, specifically those included in blocks between 2009 and 2012.

The Dataset is divided into 4 files:

- **transactions.csv**: It contains all the transactions (one per row) with various fields (timestamp, blockId, txId, isCoinbase, fee).
- **inputs.csv**: It includes a row for each input field of every transaction, with the following fields (txId, prevTxId, prevTxPos).
- **outputs.csv**: It comprises a row for each output field of every transaction, with the following fields (txId, position, addressId, amount, scripttype).
- **mapping.csv**: It serves as a mapping file for addresses, associating an address with its hash, and includes the following fields (hash, addressId).

The project primarily consists of three sections, which are as follows:

- **Data Analysis/Mining**: Performing statistical analysis on the data and generating graphical visualizations.
- **Clustering**: Utilizing the obtained data to implement a clustering algorithm that facilitates clustering of transaction addresses into weakly connected components.
- **Web Scraping**: Once the clusters are obtained, using two different websites to attempt to de-anonymize as many clusters as possible. This involves utilizing libraries such as Beautiful Soup and Selenium to create bots that automate the search process.
Finally, the project yields results, and conclusions are drawn based on the findings.

***WARNING***: If you want to run the code without modifying the JSON files, there are two options:

- You can execute the code up to the Clustering section and stop before running the Web Scraping part.
- You can comment out the code that updates the JSON files in both methods (but be aware that this will significantly increase the execution time of the code, taking around 6-7 minutes per scraping method).


## Analysis

The analysis part is divided into 5 points:

1. **Distribution of the number of transactions per block (block occupancy) over the entire considered time period**: To perform this analysis, I grouped the transactions based on the 'blockId' field and applied the `size()` function. Then, I created a plot with an additional subplot showing the cumulative distribution of transactions based on the block ID. I calculated the cumulative sum of transactions using the `np.cumsum()` function and represented it in the second subplot, sharing the x-axis between the two subplots (`sharex = True`). I added grids to both subplots and a legend for each subplot to indicate the lines being plotted.

2. **Evolution of block occupancy over time, considering two-month intervals**: I started by creating a range of dates with a monthly frequency (resulting in pairs of two months) from the date *2009-01-03* to *2012-12-31* using the Pandas library's `date_range()` function. For each date pair, I selected the transactions between them and grouped them by 'blockId', calculating the average distribution. Then, I identified the first month of each pair and grouped the month pairs in a grouped bar plot to visualize their distribution over the four years. It can be observed that the number of transactions increased over the years, especially from 2011 onwards.

3. **Total amount of UTXOs (Unspent Transaction Outputs) at the time of the last recorded transaction in the considered blockchain**: Since each transaction consists of multiple inputs and outputs, to calculate the total sum of UTXOs, I needed to keep track of the position of each output to merge them with the inputs and obtain all the spent outputs. I then subtracted the total sum of the 'amount' field from the spent outputs from the total sum of the 'amount' field of all outputs, resulting in the total sum of UTXOs. By calculating the total sum of amounts, spent amounts, and the total sum of UTXOs, I represented their distribution through a graph. It shows that only *0.3%* of the total is UTXOs, while *49.7%* has been spent.

4. **Distribution of time intervals between the transaction that generates an output and the transaction that spends it, for the spent outputs in the considered period**: First, I created two separate DataFrames where I merged inputs and transactions based on the 'prevTxId' field (to obtain all transactions created from an output) in one DataFrame, and I merged inputs and transactions based on the 'txId' field (to obtain the date when a particular output became an input and was spent) in the other DataFrame. By merging these two DataFrames, I obtained both columns, which I named 'Creation date' and 'Spent date'. I calculated the difference between these two columns to obtain the time interval between the creation and spending of an output. There may be transactions with a negative 'Days between' field, so I updated transactions and time_between to consider only transactions with a positive 'Days between' field. Finally, I performed a `groupby()` on the day difference and calculated the `size()` to plot the results. The graph indicates that most outputs are spent within a few days of their creation.

5. **Optional statistic**: For the optional statistic, I decided to propose three different versions to avoid it being too simplistic. I presented the following:

    a. *Distribution of fees for each transaction*: I calculated the positive and zero fees for each transaction and plotted the resulting graph using a pie chart to show the proportion of positive and zero fees. Testing the code on both the complete dataset and a reduced version, I noticed that the number of transactions with zero fees is very low compared to those with positive fees in the complete dataset, but the number of positive fees decreases as the dataset size decreases. Therefore, the proportion becomes nearly equal for both types of fees.

    b. *Distribution of positive and negative fees for each transaction, grouped by year*: Similar to the previous point, I extracted transactions with positive fees and zero fees from all transactions. I grouped them by year and calculated the `size()` for each year. I plotted both results using a stackplot to compare them and observe the trend of fees over the years. It can be noted that the number of transactions with both zero and positive fees increases rapidly over the years, especially from 2011 onwards.

    c. *Correlation between the cost of an output and the paid fee, and a heatmap of the correlation between some fields in the dataset*: I performed a simple merge between outputs and transactions and selected only the 'amount' and 'fee' columns. I then calculated the correlation between these two columns and plotted it using an scatter plot. Additionally, below the scatter plot, there is a heatmap showing the correlation between some fields in the dataset (calculated using the Pearson correlation provided by Pandas `corr()`). Initially, I created the heatmap using all the data, but later I removed the data that, in my opinion, did not significantly affect the overall correlation. It can be observed that the correlation between 'amount' and 'fee' is very low, indicating that the cost of an output does not influence the paid fee. In a heatmap, values range from -1 to 1, and when the correlation coefficient is close to 1, it indicates a strong positive correlation (an increase in one variable corresponds to an increase in the other), while a correlation coefficient close to -1 indicates a strong negative correlation (an increase in one variable corresponds to a decrease in the other). Therefore, I simply removed the data that had a correlation coefficient close to 0 and were not correlated.
## Clustering

Before proceeding with the implementation of the address clustering algorithm, I need to perform two merges. The first merge is between "inputs" and "transactions" on the 'txId' field to obtain all transactions and inputs with the same ID. I then apply a `groupby()` on the "txId" field and count the corresponding number of inputs associated with each transaction. At this point, I select from the DataFrame only the transactions with a strictly greater number of inputs than 1, as transactions with 1 or 0 inputs (Coinbase) do not contribute to the cluster calculation and de-anonymization. Next, I merge the previously obtained DataFrame with "outputs" (considering the positions) to obtain the 'addressId' field for each input. Finally, I use `groupby()` on 'txId' and 'addressId' and apply the `list()` function to all the addresses related to a specific ID. The clustering algorithm proceeds with the following logic:

    1. Add all possible nodes (addresses) to the graph.
    2. For each list of addresses contained in `transactions_addresses.values()`:
        Take the first element of the list and connect it to all the other elements 
        of the list using the `add_edge(x, y)` function, which adds an edge between 
        node x and node y (each address is a node, and each edge represents a path
        connecting two nodes). It is important to check if the edge we want to add is 
        not already present in the graph and that we are not connecting a node to itself   
        (self-loop) for efficiency reasons.
    3. Calculate the weakly connected components of the graph.

Once the graph is constructed and the weakly connected components are computed using the `nx.weakly_connected_components()` method provided by the NetworkX library, we obtain a generator object representing the weakly connected components (*clusters*) of the graph. I create an ordered copy of the components and a list containing the size of each cluster to then obtain the 10 largest clusters. I have also implemented a hash function that, given an address, returns its corresponding hashed value correctly using the provided mapping file. Therefore, after obtaining the 10 largest clusters, I simply apply a `map()` to each address within each cluster to obtain its corresponding hashed value. This allows me to obtain the 10 largest clusters with their hashed addresses and proceed to the Web Scraping phase without having to hash every address before attempting de-anonymization, thus saving time and resources.

Next, I calculate some values to perform descriptive statistics on the obtained clusters, such as the maximum, minimum, and mean cluster size. I then plot the distribution of the cluster sizes. It can be observed that the clusters have relatively similar sizes, and there are approximately 5 million clusters since many clusters consist of a single address. This is because at the first step of the clustering algorithm, I added all possible nodes (addresses) to the graph using the `add_nodes_from()` function, even though those with a size of 1 do not affect the subsequent calculations. Subsequently, it is necessary to create all possible edges between the addresses without creating self-loops or adding existing edges and compute the weakly connected components.
## Web Scraping

In this section, the main goal is to attempt to de-anonymize as many addresses as possible in order to associate each cluster with a specific Wallet (or Service). This is made possible by the 10 largest clusters obtained in the previous step using the address clustering algorithm. However, this alone is not sufficient to solve the problem. I need to use two websites that specialize in de-anonymizing addresses and returning their associated wallet addresses. Of course, I will not manually visit the websites and perform the searches. After careful analysis of both sites, I have gathered the necessary information to automate the process through web scraping using code.

The two websites are:

- [Wallet Explorer](https://www.walletexplorer.com/): This site allows searching for an address and returns the associated wallet address. It also provides the number of transactions made from that address and the number of addresses linked to that wallet address. Upon reaching the homepage, I noticed a simple interface with a search bar in the center of the screen and a "Search" button to initiate the searches. After conducting several searches to understand how the page responded, I concluded that it is sufficient to perform a `get()` request to the relevant page corresponding to the address I want to search for. I add the query parameter `q = address` to the URL, where "address" is the *i-th* address contained in the *j-th* cluster. Using the **BeautifulSoup** library, I can extract the HTML code of the page and locate the tag that contains the wallet address. In this case, once we are on the page related to the wallet of the address, the wallet address is located within the first *h2* tag. If the tag is present, I extract the wallet name using a personally implemented function. If the name does not start with "[", it means that the website was able to de-anonymize the address, and I can associate the wallet name found with the *j-th* cluster. I store the (cluster: wallet) pair in a dictionary and stop. If none of the addresses can be de-anonymized, then the cluster is associated with the wallet "Unknown". After numerous attempts, I realized that de-anonymizing a large-sized cluster is quite challenging. If the algorithm fails to find the wallet name immediately, it would need to continue searching until it reaches the last element of the cluster. This would be a computationally expensive search, with a worst-case complexity of **O(n)**, where *n* is the number of addresses in a cluster. Furthermore, the actual time taken by the machine to perform the search can depend on external factors such as internet connection and the website's loading speed. Searching until the last element of the cluster would be highly time-consuming and may encounter another problem I personally encountered: if the site detects an excessive number of requests, it returns a *status code* 429 indicating an error "Too many requests". To handle this, I exit the loop upon receiving this error and print the problem to the console. To overcome this issue, I introduced a 5-second time interval between each request, mimicking human-like behavior. I also added a maximum number of attempts that the algorithm can make if it continues to fail in finding a wallet for a particular cluster, and I set this limit to 15. Unfortunately, this slightly increases the execution time, but it ensures that I de-anonymize as many clusters as possible, including the last cluster.

- [Bitcon Info Charts](https://bitinfocharts.com/): The reasoning and functionalities of this website are very similar to those of Wallet Explorer, but the search page is slightly more complex. After analyzing the page, I realized that I could construct the `get()` query simply by appending *"bitcoin/address"* (where address is the address I want to de-anonymize) to the initial page URL. The de-anonymization algorithm works almost identically to Wallet Explorer, with the difference that I use **Selenium** to automate the search process and extract the wallet name. With Selenium, the difference lies in the fact that we simulate human-like behavior, increasing the chances of not being recognized as a bot. To function properly, I need to use a *WebDriver*, which allows the code to communicate with the browser's driver (each browser has a different driver). Since HTML pages sometimes take time to execute JavaScript code or load content, if we attempt to extract information through scraping immediately, we may not obtain anything. For this reason, WebDriver implements two synchronization mechanisms (implicit and explicit):

    - Implicit synchronization: The driver repeats the search at regular time intervals (*polling*) for a certain period. Once set, it remains valid as long as the WebDriver object on which it is invoked remains active. `driver.implicitly_wait(time)`
    - Explicit synchronization: The executing thread waits until a condition is met. Execution resumes if the condition becomes true or if the timeout expires. `WebDriverWait(driver, time).until(condition)`

    In this case, I need to use explicit synchronization to wait for the wallet name to be fully loaded before extracting it. To achieve this, I use the `presence_of_element_located()` function (passing it the relevant XPath of the desired tag), which returns the element if it is present or not in the page. Once the element is present on the page, I can extract the wallet name and associate it with the *j-th* cluster. By observing the code execution, I noticed that sometimes the wallet name is never loaded even after waiting for a long time. In such cases, after 10 seconds of waiting, I conclude that the page failed to load the wallet name, and I simply skip the current iteration and move on to the next address.

    From this website, I encountered several "issues" as I immediately noticed that it is much faster than Wallet Explorer in de-anonymizing addresses. However, after successfully de-anonymizing four clusters, I encountered a "block" from the website that prevented me from making further requests. The site employs a Cloudflare CAPTCHA to prevent excessive requests and can recognize whether the requester is a bot or not. In my case, I had to wait for a long time before being able to test the code again (and I bypassed the CAPTCHA with a VPN). Subsequently, I added a 5-second time interval between each request for the following attempts.

In both cases, I save the obtained results in a JSON file (a separate file for each method). The advantage of attempting to de-anonymize addresses through two different websites is that it is highly likely that if one of them fails to de-anonymize a particular address, the other website may succeed. This way, I increase the chances of de-anonymizing as many addresses (clusters) as possible, ensuring that I cover the last cluster as well.
## Conclusions

Regarding the Web Scraping part, after careful analysis and multiple code executions, I have reached the following conclusions:

- The time taken to de-anonymize the addresses is quite high (around 6-7 minutes) for both methods. This could be reduced by simply decreasing the time interval between each request (although finding a time that allows all requests without triggering the error of too many requests would be challenging), or by reducing the maximum number of attempts the search algorithm can make before concluding that it failed to find a wallet name. However, the latter solution may result in a lower number of de-anonymized clusters.

- Using two different websites for de-anonymization allows for de-anonymizing more distinct addresses, but it also introduces inconsistencies. Based on the results I obtained, some clusters are not associated with the same wallet name by both methods. A useful strategy would be to attempt to de-anonymize the clusters that one method failed to de-anonymize using the other method. In the results at the end of the notebook, the wallet names highlighted in bold are the ones that were de-anonymized identically by both methods.

### Results Obtained

Wallet Explorer:

- Cluster 1: CoinJoinMess
- Cluster 2: **SilkRoadMarketplace**
- Cluster 3: Unknown wallet name
- Cluster 4: **Instawallet.org**
- Cluster 5: BTC-e.com-old
- Cluster 6: Unknown wallet name
- Cluster 7: BtcDice.com
- Cluster 8: Unknown wallet name
- Cluster 9: Unknown wallet name
- Cluster 10: **Bitcoin.de-old**

Bitcoin Info Charts:

- Cluster 1: F2Pool
- Cluster 2: **SilkRoadMarketplace**
- Cluster 3: Unknown wallet name
- Cluster 4: **Instawallet.org**
- Cluster 5: Eligius
- Cluster 6: Unknown wallet name
- Cluster 7: Unknown wallet name
- Cluster 8: Unknown wallet name
- Cluster 9: Unknown wallet name
- Cluster 10: **Bitcoin.de-old**

### Some information about the de-anonymized wallets

**CoinJoin** is a privacy method used in cryptocurrency transactions, such as Bitcoin. It involves combining multiple transactions into a single combined transaction, making it more difficult to trace the relationships between different sender and recipient addresses. For example, if Alice, Bob, and Charlie want to send Bitcoin to different recipients, they can use CoinJoin to combine their transactions into a single transaction that includes payments from all three. This way, it becomes challenging for external observers to determine who sent Bitcoin to which recipient, as the transactions have been mixed together. It is important to note that CoinJoin is not a built-in feature in the Bitcoin protocol itself but rather a technique implemented by third-party services and software.

**F2Pool** is one of the largest and most popular cryptocurrency mining pools in the world. It was one of the first mining pools to support the mining of Bitcoin and other cryptocurrencies. As a mining pool, F2Pool provides a shared infrastructure where cryptocurrency miners can pool their computational resources to increase the chances of successfully mining blocks. Cryptocurrency mining involves solving complex mathematical problems to confirm transactions and ensure network security. Miners who successfully solve these problems are rewarded with newly issued coins and transaction fees. One distinctive feature of F2Pool is its size and significant hash power. Hash power refers to the combined computing power of miners within a pool.

**SilkRoadMarketplace** was an e-commerce website that operated through the hidden services of the anonymity software *Tor*. Only through Tor, it was possible to access the site. Various products sold on Silk Road are classified as contraband in most jurisdictions worldwide. Silk Road has been referred to as the "Amazon of drugs." On October 3, 2013, Silk Road was shut down by the FBI. In early November, it was announced to be reopened by the pseudonym Dread Pirate Roberts, even though the FBI had arrested the person they believed to be behind that name. On November 6, 2014, Silk Road was permanently shut down by the FBI.

**Instawallet** was a past eWallet that required access and spending of funds in the wallet solely through the website address (URL). This allowed for anonymous use of the service without even requiring an email address. The site included a warning notice stating, "Instawallet is not designed to be a Bitcoin bank and therefore can only provide a medium level of security. Please do not store more than pocket change here."

**BTC-e** was a cryptocurrency trading platform primarily targeting the Russian audience, with servers located in the United States, until the US government seized their website and all funds in 2017. Until 2015, it handled approximately 3% of all Bitcoin exchange volume.

**Eligius** is a mining pool. To use it, a miner simply needs to point to *stratum.mining.eligius.st* on port 3334, with the username set to a valid Bitcoin address (to receive the payment). No registration is required, and the basic concepts are as follows:

- The pool does not charge any fees
- When a block is found, all miners who have reached the minimum payment threshold are paid via the generation transaction
- The pool almost never holds miners' funds since they are paid directly to miners from the block reward
- If a block becomes "orphaned," its shares become part of the next block reward distribution
- No registration is required; Bitcoin addresses are used as usernames

**BtcDice** was a website dedicated to Bitcoin-based gambling. It offered an online dice game service, where users could bet and win Bitcoin. The operation of BtcDice was quite simple: users could enter a quantity of Bitcoin as a bet and select a numerical value to bet on. Subsequently, the site randomly generated a number, and if the generated number was lower than the value selected by the user, they would win the bet and receive a quantity of Bitcoin according to the game's rules.

**Bitcoin.de** is a marketplace where Bitcoin is traded directly between users and acts as a trustee for the Bitcoin offered on the site. It is also possible to use the account as an online wallet for Bitcoin. Currently, it offers the service of exchanging between Bitcoin and Euro. The supported payment methods are bank transfer, SEPA, and Moneybookers.

## Documentation

Used libraries:

- [Pandas](https://pandas.pydata.org/docs/index.html)
- [Mathplotlib](https://matplotlib.org/stable/)
- [Seaborn](https://seaborn.pydata.org/#)
- [Numpy](https://numpy.org/doc/stable/)
- [NetworkX](https://networkx.org/)
- [Requests](https://docs.python-requests.org/en/latest/index.html)
- [Beautiful Soup](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
- [Selnium](https://www.selenium.dev/documentation/)
- [JSON](https://docs.python.org/3/library/json.html)


## Installation

You have to install each library you see on the import's section with this command:

```bash
    pip install library
```

Or if you have **pip3** installed:

```bash
    pip3 install library
```
    
## Authors

- [@Mxo01](https://www.github.com/Mxo01)

