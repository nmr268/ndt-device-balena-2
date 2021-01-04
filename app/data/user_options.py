# -*- coding: utf-8 -*-
"""Define user_options, could also be kept in a file"""

__copyright__ = "Copyright (C) 2020 Nordetect"

options = [
	{
	"option": "Use_barcode",
	"help_text": "Choose whether are using barcodes to identify the samples",
	"label": "Use Barcode",
	"choice": [
			{
			"choice_id" : 1,
			"label" :  "Yes",
            "int_rep" : True
			},
	 		{
			"choice_id": 2,
			"label": "No",
            "int_rep" : False
            }
		   ],
	 "default": 1
	},
	{
	"option": "model_type",
	"help_text": "Choose an Analysis Type",
	"label": "Analysis Type",
	 "choice": [
			{
			"choice_id" : 1,
			"label" :  "Soil",
            "int_rep" : "soil"
			},
	 		{
			"choice_id": 2,
			"label": "Water",
            "int_rep" : "water"
            }
		   ],
	 "default": None
	}
]
