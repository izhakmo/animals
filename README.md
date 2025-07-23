Some decisions were not well defined, this is how i handled them
* some animals had an invalid `Collateral adjective` ==> I saved them to a file called `rows_with_invalid_types.log`
  * in addition - i added them under a new type: `undefined type`
* i created a file named `lists_log.log` that contains animals that had another page with a list
  * addition that can be done - we could iterate over it and add list of animals, and the pictures (though the format of these pages are not same for all the files)
* in a real system i would use a message broker such as kafka, to consume download image events
* i printed errors to log_file named `image_download_errors.log` and also to consule


modules that were used:
* `image_downloader.py` - handle the image, download it
* `report_generator.py` - generate the html report file
* `web_scrapper.py` - get the table of data from the web page
* `pipeline.py` - main flow
* `constants.py`
* (ut file)

* how to use - `pip install -r requirements.txt` then run `main.py`
