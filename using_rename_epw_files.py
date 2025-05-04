#!/usr/bin/env python
# coding: utf-8

# # Using ``rename_epw_files()`` to rename the EPWs for proper data analysis after simulation

# ``rename_epw_files`` function will rename your EPW files following the naming convention "Country_City_RCPscenario-Year". It will get the Country and City fields from EPW coordinates, and the RCPscenario and Year fields from the original name. If there is no reference to this in the original name, it will consider these to be at Present scenario.

# usage:
# ``
# rename_epw_files(  
# filelist=list_of_files_to_rename, # if omitted, it will rename all EPWs in that folder  
# confirm_renaming=True or False, #to skip renaming confirmation on prompt command or console  
# confirm_deletion=True or False #to skip deletion confirmation on prompt command or console  
# match_cities: True or False. Default is False. It's computationally very expensive.  
# )``

# First of all, let's see what files we do have in the folder:

# In[1]:


import os
os.listdir()

previous_files = [i for i in os.listdir()]


# You can see there are 3 EPW files, which are:

# In[2]:


old_epws = [i for i in os.listdir() if i.endswith('.epw')]
print(old_epws)


# So let's rename them. When we call the function, you will be asked to enter the IDs of the EPW names which are not correct, if there are any. If you enter one or multiple IDs, you will be asked if you want to rename them manually (i.e. typing the correct new name) or not. If you say 'n', possible names will be searched by using the geolocation, which can be computationally expensive if there are a moderate number of EPWs (e.g. 30).

# In[3]:


from accim.data.preprocessing import rename_epw_files
rename_epw_files(
    confirm_deletion=False,
)


# You can see above that there was no reference to RCP scenarios in the original EPW file name in 2 of the instances, therefore these has been considered as Present scenario. The same applies to the Year field. Finally, states the previous and the new names of the EPWs. So, now, let's see what files we do have in the folder.

# In[ ]:


os.listdir()


# We can see the new EPWs are:

# In[ ]:


new_epws = [i for i in os.listdir() if not(any(i in j for j in old_epws)) and i.endswith('.epw')]
print(new_epws)


# Let's delete the new files so that we can run the notebook again.

# In[ ]:

new_files = [i for i in os.listdir() if i not in previous_files]
# for i in new_files:
#     os.remove(i)

# for i in new_epws:
#     os.remove(i)

