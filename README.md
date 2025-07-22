Some decisions were not well defined, this is how i handled them
* some animals had an invalid `Collateral adjective` ==> I saved them to a file called `rows_with_invalid_types.log`
  * in addition - i added them under a new type: `undefined type`

additions that can be done:
* there is file named `animals_with_lists.log` ==> we could iterate over it and add list of animals, and the pictures (though the format of these pages are not same for all the files)
* in a real system i would use a message broker such as kafka, to consume download image events


TODOS:
* add comments
* explain what has been done
* update readme
