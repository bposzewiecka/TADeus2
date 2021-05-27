$('.subtracks tr').each( function() {
    elems = $(this).find('td')

    text = '"","' + $(elems[1]).attr('bgcolor') + '",'

    text += '"' + $(elems[2]).text().trim() + '","",'

    text += '"' +  $(elems[3]).text().trim() + '",'

    elem4 = $(elems[4]).find('a')[0]

    if (elem4) {
        href_el = $(elem4).attr('href').split('&') 

        href1 = href_el[1].split('=')[1]
        text += '"' + href1 + '",'

        href2 = href_el[2].split('=')[1]
        text += '"' + href2 + '",'

        href3 = href_el[3].split('=')[1]
        text += '"' + href3 + '",'
    }

    console.log(text)
})


$('.subtracks tr').each( function() {
    elems = $(this).find('td')

    text = '"","' + $(elems[1]).attr('bgcolor') + '",'

    elem2 = $(elems[2]).find('a')[0]

    if ($(elems[2]).html()) {
        text += '"' + $(elem2).text().trim() + '",'
        text += '"' + $(elem2).attr('title') + '",'
    } else {
        text += '"' + $(elem2).text() + '","",'
    }

    text += '"' + $(elems[3]).text().trim() + '",'
    text += '"' + $(elems[4]).text().trim() + '",'

    elem5 = $(elems[5]).find('a')[0]

    if (elem5) {
        href_el = $(elem5).attr('href').split('&') 

        href1 = href_el[1].split('=')[1]
        text += '"' + href1 + '",'

        href2 = href_el[2].split('=')[1]
        text += '"' + href2 + '",'

        href3 = href_el[3].split('=')[1]
        text +=  '"' + href3+ '",'
    }

    console.log(text)
})



$('.subtracks tr').each( function() {
    elems = $(this).find('td')

    text = '"' + $(elems[2]).text().trim() + '",'
    text += '"' + $(elems[3]).attr('bgcolor') + '",'

    elem4 = $(elems[4]).find('a')[0]

    if ($(elems[4]).html()) {
        text += '"' + $(elem4).text() + '",'
        text += '"' + $(elem4).attr('title') + '",'
    } else {
        text += '"' + $(elem4).text() + '","",'
    }

    text += '"' + $(elems[5]).text().trim() + '",'

    text += '"' + $(elems[6]).text().trim() + '",'

    elem7 = $(elems[7]).find('a')[0]

    if (elem7) {
        href_el = $(elem7).attr('href').split('&') 

        href1 = href_el[1].split('=')[1]
        text += '"' + href1 + '",'

        href2 = href_el[2].split('=')[1]
        text += '"' + href2+ '",'

        href3 = href_el[3].split('=')[1]
        text += '"' + href3+ '",'
    }

    console.log(text)
})