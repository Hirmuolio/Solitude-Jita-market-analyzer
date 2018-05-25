# Solitude-Jita-market-analyzer

This tool will import full market data for Solitude region + Gravity Well and The Forge region (Jita).
Then it compares the prices and exports the analyzed data to "export.txt" file.

The text file will contain in this order:
Item name
Jita sell price / Solitude sell price
Jita buy price / Solitude sell price

If "Jita sell price / Solitude sell price" is smaller than 1 then it is cheaper to buy in Jita than in Solitude. Opportunity to import things.
If "Jita sell price / Solitude sell price" is greater than 1 then it is cheaper to buy in Solitude than in Jita. Opportunity to buy and relist things.
If  "Jita sell price / Solitude sell price " is equal to 1 then the prices are same.

If "Jita buy price / Solitude sell price" is greater than 1 then you can buy from Solitude and instantly sell in Jita for profit.

It will also list items that are not sold in Solitude. Check them and maybe import some.

The script also has filtering options. You can filter by meta level and by category.

### How to get the tool working
Requires python 3 and requests http://docs.python-requests.org/en/master/

Since the script imports orders from our citadel you will need to do some extra steps to get the script working.

1) Register as developer at https://developers.eveonline.com
2) Create new application with scope: `esi-markets.structure_markets.v1` and redirect url: `http://localhost/oauth-callback`
3) Run the script. It will ask for client ID and client secret. You get them from the application you registered.
4) Login window will open. Log in with a character that can access Gravity Well.
Once you log in you will be redirected to page `http://localhost/oauth-callback?code=[your code is here]`. Copy the [your code is here] part into the tool window when it is asked for.

The above needs to be done only once.

Then just import market data (may take a while). you can also load old data if you already imported maraket data.

Once importing is completed you can export the data or change the filters.

The tool is future proof. If new items are added the script will fetch their info from API. Though it will not update old items so if items are renamed or moved to new categories the script will use old info. If some update adds new categories just delete "categories.json" to reload categories from API.
