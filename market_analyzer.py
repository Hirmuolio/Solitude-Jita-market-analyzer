#!/usr/bin/env python3

import json
import sys

import esi_calling

esi_calling.set_user_agent('Hirmuolio/Solitude-Jita-market-analyzer')

def import_orders(region_id):
	#'10000044' Solitude
	print('importin page 1')
	all_orders = []
	
	response = esi_calling.call_esi(scope = '/v1/markets/{par}/orders/', url_parameter=region_id, job = 'get market orders')
	
	all_orders.extend(response.json())
	total_pages = int(response.headers['X-Pages'])
	print('total number of pages:'+str(total_pages))
	
	responses = []
	for page in range(2, total_pages + 1):
		print('\rimportin page: '+str(page)+'/'+str(total_pages), end="")
		
		response = esi_calling.call_esi(scope = '/v1/markets/{par}/orders/', url_parameter=region_id, parameters = {'page': page}, job = 'get market orders')
		
		responses.append(response)
	for response in responses:
		data = response.json()
		all_orders.extend(data)
	print('. Got {:,d} orders.'.format(len(all_orders)))
	return all_orders
		
def structure_import_orders(structure_id):
	print('importin page 1')
	market_url = "https://esi.tech.ccp.is/v1/markets/structures/"+structure_id+"/"
	all_orders = []
	
	tokens = esi_calling.check_tokens(tokens = config['tokens'], client_secret = client_secret, client_id =client_id)
	
	#Save the new tokens
	config['tokens'] = tokens
	with open('config.json', 'w') as outfile:
		json.dump(config, outfile, indent=4)
			
	response = esi_calling.call_esi(scope = '/v1/markets/structures/{par}', url_parameter=structure_id, tokens = tokens,  job = 'get citadel orders')
	
	all_orders.extend(response.json())
	total_pages = int(response.headers['X-Pages'])
	print('total number of pages:'+str(total_pages))
	
	responses = []
	for page in range(2, total_pages + 1):
		print('\rimportin page: '+str(page)+'/'+str(total_pages), end="")
		
		response = esi_calling.call_esi(scope = '/v1/markets/structures/{par}', url_parameter=structure_id, parameters = {'page': page} , tokens = tokens,  job = 'get citadel orders')
		
		responses.append(response)
	for response in responses:
		data = response.json()
		all_orders.extend(data)
	print('Got {:,d} orders.'.format(len(all_orders)))
	return all_orders
		
def get_item_prices(response):
	item_prices = {}
	for index in range(0, len(response)):
		type_id = response[index]['type_id']
	
		if not str(type_id) in item_prices:
			item_prices[str(type_id)] = {}
	
		#add price info
		if response[index]['is_buy_order'] == True:
			if 'buy_price' in item_prices[str(type_id)]:
				item_prices[str(type_id)]['buy_price'] = max(response[index]['price'], item_prices[str(type_id)]['buy_price'])
			else:
				item_prices[str(type_id)]['buy_price'] = response[index]['price']
		else:
			if 'sell_price' in item_prices[str(type_id)]:
				item_prices[str(type_id)]['sell_price'] = min(response[index]['price'], item_prices[str(type_id)]['sell_price'])
			else:
				item_prices[str(type_id)]['sell_price'] = response[index]['price']
	return item_prices

def get_item_attributes(type_id):
	#Note: type_id is string here
	
	esi_response = esi_calling.call_esi(scope = '/v3/universe/types/{par}', url_parameter=type_id, job = 'get item attributes')
	
	#Important attributes:
	#'group_id'
	#'market_group_id'
	#'name'
	#important dogma attributes
	#633 = meta level
	#422 = tech level
	#1692 = meta group id
	
	type_id_list[type_id] = {}
	
	type_id_list[type_id]['name'] = esi_response.json()['name']
	
	if 'group_id' in esi_response.json():
		type_id_list[type_id]['group_id'] = esi_response.json()['group_id']
		
	if 'market_group_id' in esi_response.json():
		type_id_list[type_id]['market_group_id'] = esi_response.json()['market_group_id']
		
	if 'dogma_attributes' in esi_response.json():
		for index in range(0, len(esi_response.json()['dogma_attributes'])):
			if esi_response.json()['dogma_attributes'][index]['attribute_id'] == 633:
				type_id_list[type_id]['meta_level'] = esi_response.json()['dogma_attributes'][index]['value']
			elif esi_response.json()['dogma_attributes'][index]['attribute_id'] == 422:
				type_id_list[type_id]['tech_level'] = esi_response.json()['dogma_attributes'][index]['value']
			elif esi_response.json()['dogma_attributes'][index]['attribute_id'] == 1692:
				type_id_list[type_id]['meta_group_id'] = esi_response.json()['dogma_attributes'][index]['value']
		
	#Save the item info list
	with open('type_id_list.json', 'w') as outfile:
		json.dump(type_id_list, outfile, indent=4)
			

def import_solitude():
	#Regions
	#'10000044' Solitude
	#'10000002' Forge (Jita)
	#'10000032' Dodixie

	#'1021628175407' GW

	#Import Solitude market
	print('Importing Solitude market')
	solitude_response = import_orders('10000044')
	print('\nImporting Gravity Well market')
	solitude_response.extend( structure_import_orders('1021628175407') )
	solitude_prices = get_item_prices(solitude_response)

	#Save market
	with open('solitude.json', 'w') as outfile:
		json.dump(solitude_prices, outfile, indent=4)
	
	return solitude_prices

def import_jita():
	#Import Jita
	#10000032 = dodixie
	#10000002 = Jita
	print('\nImporting Jita market')
	jita_response = import_orders('10000002')
	jita_prices = get_item_prices(jita_response)

	with open('jita.json', 'w') as outfile:
		json.dump(jita_prices, outfile, indent=4)

	
			
	return jita_prices
	
	
#-----------------------
#Start working
#----------------------


#Prepare things
#Check config and log in if needed
try:
	config = json.load(open('config.json'))
	
	try:
		client_id = config['client_id']
		client_secret = config['client_secret']
	except KeyError:
		#Config found but no wanted content
		print('no client ID or secret found. \nRegister at https://developers.eveonline.com/applications to get them')
		
		client_id = input("Give your client ID: ")
		client_secret = input("Give your client secret: ")
		config = {"client_id":client_id, "client_secret":client_secret}
		with open('config.json', 'w') as outfile:
			json.dump(config, outfile, indent=4)
except (IOError, json.decoder.JSONDecodeError):
	#no config
	print('no client ID or secret found. \nRegister at https://developers.eveonline.com/applications to get them')
	client_id = input("Give your client ID: ")
	client_secret = input("Give your client secret: ")
	#default filters:
	filtered_meta = []
	filtered_techs = []
	filtered_metagroups = [3, 4, 5, 6]
	#Meta groups:
	#3 storyline
	#4 pirate faction
	#5 officer
	#6 deadspace
	filtered_categories = [9, 5, 9, 16, 17, 23, 30, 39, 40, 46, 91, 66]
	
	config = {'client_id':client_id, 'client_secret':client_secret, 'filtered_meta':filtered_meta, 'filtered_categories':filtered_categories, 'filtered_metagroups': filtered_metagroups, 'filtered_techs': filtered_techs}
	with open('config.json', 'w') as outfile:
		json.dump(config, outfile, indent=4)
		
if not 'tokens' in config:
	#You need to log in
	
	tokens = esi_calling.logging_in(scopes = 'esi-markets.structure_markets.v1', client_id = client_id, client_secret = client_secret)
	
	config['tokens'] = tokens

	with open('config.json', 'w') as outfile:
		json.dump(config, outfile, indent=4)
		
#Load cached item data
try:
	#Load cached dogma attribute ID info
	type_id_list = json.load(open('type_id_list.json'))
except FileNotFoundError:
	#No file found. Start from scratch
	type_id_list = {}
	
#Load cached categories
try:
	categories = json.load(open('categories.json'))
except FileNotFoundError:
	#No file found. Start from scratch
	print('Importing category list...')
	
	response = esi_calling.call_esi(scope = '/v1/universe/categories/', job = 'get list of categories')

	list_categories = response.json()

	print('\rImporting category names... ')
	categories = {}
	n = 1
	for category_id in list_categories:
		#print('\rchecking item: '+str(n)+'/'+str(number_of_items)+' type ID '+key, end="")
		print( '\r'+str(n)+'/'+str(len(list_categories)), end="")
		
		response = esi_calling.call_esi(scope = '/v1/universe/categories/{par}', url_parameter = category_id, job = 'get list of categories')
		
		category_name = response.json()['name']
		categories[str(category_id)] = category_name
		n= n+1
	print('')
	with open('categories.json', 'w') as outfile:
		json.dump(categories, outfile, indent=4)

#load cached group ids
try:
	group_id_list = json.load(open('group_id_list.json'))
except FileNotFoundError:
	#No file found. Start from scratch
	group_id_list = {}
	with open('group_id_list.json', 'w') as outfile:
		json.dump(group_id_list, outfile, indent=4)

#Script starts workin here
print('starting')

start_menu = True
while start_menu:
	print('\n[I] Import market data\n[L] Load old market data')
	user_input = input("[I/L] ")

	if user_input == 'I' or user_input == 'i':
		solitude_prices = import_solitude()
		hub_prices = import_jita()
		start_menu = False
	elif user_input == 'L' or user_input == 'l':
		solitude_prices = json.load(open('solitude.json'))
		hub_prices = json.load(open('jita.json'))
		start_menu = False

#-------------
#Process imported/loaded data
#-------------

#Make sure we have the item attributes
print('getting item attributes')
number_of_items = len(solitude_prices)
n=1
for key in solitude_prices.keys():
	print('\rchecking item: '+str(n+1)+'/'+str(number_of_items)+' type ID '+key, end="")
	n=n+1
	if not key in type_id_list:
		get_item_attributes(key)
			

number_of_items = len(hub_prices)
n=1
for key in hub_prices.keys():
	print('\rchecking item: '+str(n)+'/'+str(number_of_items)+' type ID '+key, end="")
	n=n+1
	if not key in type_id_list:
		get_item_attributes(key)
			
#Compare the prices
full_id = []
full_names = []
full_sell_sell = []
full_buy_sell = []

for key in hub_prices.keys():

	name = type_id_list[key]['name']
	
	full_id.append(int(key))
	full_names.append(name)
	

	if key in solitude_prices:
		if 'sell_price' in solitude_prices[key]:
			if 'sell_price' in hub_prices[key]:				
				full_sell_sell.append(round( (hub_prices[key]['sell_price'] / solitude_prices[key]['sell_price']), 2))
				
				if 'buy_price' in hub_prices[key]:		
					full_buy_sell.append(round( (hub_prices[key]['buy_price'] / solitude_prices[key]['sell_price'] ), 2))
				else:
					#Not sold in market hub
					full_buy_sell.append(-1)
			else:				
				full_buy_sell.append(-1)
				full_sell_sell.append(-1)

		else:
			#Not sold in Solitude

			full_buy_sell.append(-1)
			full_sell_sell.append(-1)
	else:
		#No orders at all in Solitude
		
		full_buy_sell.append(-1)
		full_sell_sell.append(-1)


#Sort the lists
full_sell_sell, full_buy_sell, full_names, full_id = zip(*sorted(zip(full_sell_sell, full_buy_sell, full_names, full_id)))

filtered_meta = config['filtered_meta']
filtered_categories = config['filtered_categories']
filtered_techs = config['filtered_techs']
filtered_metagroups = config['filtered_metagroups']

metagroup_names = {'3':'storyline', '4':'faction', '5':'officer', '6':'deadspace'}

option_menu=True

print('')
while option_menu:
	print('\nMarket data ready for exporting.')
	print('\nCurrently active filters:')
	print('Meta levels filtered: ', end="" )
	for meta in filtered_meta:
		print( str(meta) + ', ', end="" )
	print('')
	
	print('Tech levels filtered: ', end="")
	for tech in filtered_techs:
		print( 'Tech ' + str(tech) + ', ', end="" )
	print('')
	
	print('Meta groups filtered: ', end="" )
	for id in filtered_metagroups:
		print( str(metagroup_names[str(id)]) + ', ', end="" )
	print('')
		
	print('Categories filtered: ' , end="")
	for category_id in filtered_categories:
		print( categories[str(category_id)]+', ', end="")
	print('')
	
	print('\n[E] Export analyzed market data\n[M] Meta level filter\n[T] Tech level filter\n[G] Meta group filter\n[C] Category filter')
	user_input = input("[E/M/C/G/T] ")

	if user_input == 'E' or user_input == 'e':
		#Just exit this and do the exporting
		option_menu = False
	elif user_input == 'M' or user_input == 'm':
		#Set filters
		#meta levels:
		#0 = T1
		#1-4 = meta
		#5 = T2
		#6- storyline, faction, ded, officer
		print('Filtered meta levels:', filtered_meta)
		user_input = input("Give meta level to include/exlude: ")
		try:
			level = int(user_input)
			if int(user_input) in filtered_meta:
				filtered_meta.remove(int(user_input))
			else:
				filtered_meta.append(int(user_input))
				filtered_meta.sort()
		
			#Save the new meta limit
			config['filtered_meta'] = filtered_meta
			with open('config.json', 'w') as outfile:
				json.dump(config, outfile, indent=4)
		except:
			print('That is not an integer')
			
	elif user_input == 'C' or user_input == 'c':
		for category_id in categories:
			if int(category_id) in filtered_categories:
				print('['+category_id+'] '+categories[category_id]+' - FILTERED')
			else:
				print('['+category_id+'] '+categories[category_id])
		user_input = input("\nGive ID of category to filter out/remove filtering: ")
		
		try:
			if user_input in categories:
				if int(user_input) in filtered_categories:
					filtered_categories.remove(int(user_input))
				else:
					filtered_categories.append(int(user_input) )
					filtered_categories.sort()
				#Save the new category filter
				config['filtered_categories'] = filtered_categories
				with open('config.json', 'w') as outfile:
					json.dump(config, outfile, indent=4)
			else:
				print('no category: '+user_input)
		except:
			print('That is not an integer.')
	elif user_input == 'G' or user_input == 'g':
		#filter meta groups
		# 3 = storyline
		# 4 = faction
		# 5 = officer
		# 6 = deadspace
		
		print('\nMeta groups:')
		for id in range(3,6+1):
			if id in filtered_metagroups:
				print('[' + str(id)+ '] - ' + metagroup_names[str(id)] + ' - FILTERED')
			else:
				print('[' + str(id)+ '] - ' + metagroup_names[str(id)] )
				
		user_input = input("\nGive ID of meta group to filter out/remove filtering: ")
		try:
			if int(user_input) in [3, 4, 5, 6]:
				if int(user_input) in filtered_metagroups:
					filtered_metagroups.remove(int(user_input))
				else:
					filtered_metagroups.append(int(user_input) )
					filtered_metagroups.sort()
				#Save the new category filter
				config['filtered_metagroups'] = filtered_metagroups
				with open('config.json', 'w') as outfile:
					json.dump(config, outfile, indent=4)
			else:
				print('no category: '+user_input)
		except:
			print('That is not an integer.')
			
	elif user_input == 'T' or user_input == 't':
		#Tech level filter
		print('\nTech levels:')
		for tech in range(1,3+1):
			if tech in filtered_techs:
				print('Tech ' + str(tech)+ ' - FILTERED')
			else:
				print('Tech ' + str(tech))
				
		user_input = input("\nGive tech level to filter out/remove filtering: ")
		try:
			if int(user_input) in [1, 3, 4]:
				if int(user_input) in filtered_techs:
					filtered_techs.remove(int(user_input))
				else:
					filtered_techs.append(int(user_input) )
					filtered_techs.sort()
				#Save the new category filter
				config['filtered_techs'] = filtered_techs
				with open('config.json', 'w') as outfile:
					json.dump(config, outfile, indent=4)
			else:
				print('no tech level: '+user_input)
		except:
			print('That is not an integer.')
		

print('Formatting data for exporting...')
#Export analyzed market data
output = ''
for index in range(0, len(full_sell_sell)):
	if full_sell_sell[index] == -1:
		out_sell_sell = 'Not sold in Solitude'
	else:
		out_sell_sell = full_sell_sell[index]
	
	if full_buy_sell[index] == -1:
		out_buy_sell = ''
	else:
		out_buy_sell = full_buy_sell[index]
	
	#if the item has meta level apply meta level filter
	if 'meta_level' in type_id_list[str(full_id[index])] and type_id_list[str(full_id[index])]['meta_level'] in filtered_meta:
		line = ''
	#if item has tech level apply tech filter
	elif 'tech_level' in type_id_list[str(full_id[index])] and type_id_list[str(full_id[index])]['tech_level'] in filtered_techs:
		line = ''
	#if item has meta group apply meta group filter
	elif 'meta_group_id' in type_id_list[str(full_id[index])] and type_id_list[str(full_id[index])]['meta_group_id'] in filtered_metagroups:
		line = ''
		
	#if the item has group id apply category filter
	elif 'group_id' in type_id_list[str(full_id[index])]:
	
		group_id = type_id_list[str(full_id[index])]['group_id']
		
		if not str(group_id) in group_id_list:
			#Import group id info and save it
			print('importing category for group ID: ', group_id)
			
			response = esi_calling.call_esi(scope = '/v1/universe/groups/{par}', url_parameter=group_id, job = 'get category for groupo id')
			
			category_id = response.json()['category_id']
			
			group_id_list[str(group_id)] = category_id
			
			with open('group_id_list.json', 'w') as outfile:
				json.dump(group_id_list, outfile, indent=4)
				
		category_id = group_id_list[str(group_id)]
		
		if category_id in filtered_categories:
			line = ''
		else:
			line = '{:<50s} {:<10s} {:<10s}'.format(full_names[index], str(out_sell_sell), str(out_buy_sell)) + '\n'
				
	else:
		line = '{:<50s} {:<10s} {:<10s}'.format(full_names[index], str(out_sell_sell), str(out_buy_sell)) + '\n'
	#output = output + full_names[index] + '\t' + str(out_sell_sell) + '\t' + str(out_buy_sell) + '\n'
	output = output + line
	#input("enter...")

print('Exporting to file')	
with open('export.txt', "w") as text_file:
	print(output.encode("utf-8"), file=text_file)

user_input = input("Market analysis exported to export.txt. Press enter to exit.")
