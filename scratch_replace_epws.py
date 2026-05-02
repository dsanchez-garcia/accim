import sys

with open('d:/Python/accim/accim/parametric_and_optimisation/main.py', 'r', encoding='utf-8') as f:
    content = f.read()

target = "        :return: pandas DataFrame containing the results of the optimisation (the specific solutions depend on keep_df).\n        \"\"\"\n        import warnings"
replacement = "        :return: pandas DataFrame containing the results of the optimisation (the specific solutions depend on keep_df).\n        \"\"\"\n        self.epws = epws\n        import warnings"

content = content.replace(target, replacement)

with open('d:/Python/accim/accim/parametric_and_optimisation/main.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Replaced successfully')
