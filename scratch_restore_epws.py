import sys

with open('d:/Python/accim/accim/parametric_and_optimisation/main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# For parametric load
target_param = """            if payload.get('idf_backup_path'):
                self.idf_backup_path = payload['idf_backup_path']
                print(f'  [info] idf_backup_path restored: {self.idf_backup_path}')"""
replacement_param = target_param + """
            if payload.get('epws'):
                self.epws = payload['epws']
            elif self.outputs_param_simulation.attrs.get('epws'):
                self.epws = self.outputs_param_simulation.attrs['epws']"""

# Note that for pickle, attrs is preserved, so we should extract it from attrs.
# Wait, let's just do it at the end of the method:
# self.epws = self.outputs_param_simulation.attrs.get('epws', [])

# Same for optimisation.

content = content.replace("self.last_run_type = 'parametric'", "self.epws = self.outputs_param_simulation.attrs.get('epws', [])\n        self.last_run_type = 'parametric'")
content = content.replace("self.last_run_type = 'optimisation'", "self.epws = self.outputs_optimisation.attrs.get('epws', [])\n        self.last_run_type = 'optimisation'")

with open('d:/Python/accim/accim/parametric_and_optimisation/main.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Restored epws loading successfully')
