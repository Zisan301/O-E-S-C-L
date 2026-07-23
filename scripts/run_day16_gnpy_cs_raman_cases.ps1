$ErrorActionPreference = 'Stop'

Write-Host 'Running C+S Raman/ISRS case: -2 dBm'
gnpy-transmission-example validation_data/gnpy_CS_12span_full_raman_network.json -e validation_data/gnpy_day11_equipment.json --sim-params validation_data/gnpy_day16_raman_sim_params.json --spectrum validation_data/gnpy_CS_day16_full_cs_spectrum.json --show-channels -po -2 *> validation_data/gnpy_day16_cs_raman_logs\CS_m2dBm.txt
Write-Host 'Running C+S Raman/ISRS case: 0 dBm'
gnpy-transmission-example validation_data/gnpy_CS_12span_full_raman_network.json -e validation_data/gnpy_day11_equipment.json --sim-params validation_data/gnpy_day16_raman_sim_params.json --spectrum validation_data/gnpy_CS_day16_full_cs_spectrum.json --show-channels -po 0 *> validation_data/gnpy_day16_cs_raman_logs\CS_0dBm.txt
Write-Host 'Running C+S Raman/ISRS case: 2 dBm'
gnpy-transmission-example validation_data/gnpy_CS_12span_full_raman_network.json -e validation_data/gnpy_day11_equipment.json --sim-params validation_data/gnpy_day16_raman_sim_params.json --spectrum validation_data/gnpy_CS_day16_full_cs_spectrum.json --show-channels -po 2 *> validation_data/gnpy_day16_cs_raman_logs\CS_2dBm.txt
Write-Host 'Running C+S Raman/ISRS case: 4 dBm'
gnpy-transmission-example validation_data/gnpy_CS_12span_full_raman_network.json -e validation_data/gnpy_day11_equipment.json --sim-params validation_data/gnpy_day16_raman_sim_params.json --spectrum validation_data/gnpy_CS_day16_full_cs_spectrum.json --show-channels -po 4 *> validation_data/gnpy_day16_cs_raman_logs\CS_4dBm.txt
