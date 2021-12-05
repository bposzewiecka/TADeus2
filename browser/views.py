from django.shortcuts import render

def image(request, p_cols, p_id, p_chrom, p_start, p_end, p_breakpoint_id = None, p_left_side = None, p_width_prop = None):
    
    p_start = int(p_start)

    track = Track.objects.get(id = p_id)
    breakpoint = None

    p_name_filter = None

    if request.method == 'GET': 
        name_filter = request.GET.get('name_filter', None)
        interval_start = request.GET.get('interval_start', '')

        if interval_start:
            interval_start = int(interval_start)

        interval_end = request.GET.get('interval_end', '')

        if interval_end:
            interval_end = int(interval_end)

        if p_breakpoint_id:
            breakpoint = Breakpoint.objects.get(id = p_breakpoint_id)

        breakpoint_coordinates = {}
        breakpoint_coordinates['left_start'] = int(request.GET.get('left_start', '-1'))
        breakpoint_coordinates['left_end'] = int(request.GET.get('left_end', '-1'))
        breakpoint_coordinates['right_start'] = int(request.GET.get('right_start', '-1'))
        breakpoint_coordinates['right_end'] = int(request.GET.get('right_end', '-1'))

    fig = track.draw_track(p_cols, chrom = p_chrom, start = p_start, end = p_end, 
        interval_start = interval_start, interval_end = interval_end, name_filter = name_filter,  
        breakpoint = breakpoint, left_side = p_left_side, 
        width_prop = p_width_prop, breakpoint_coordinates = breakpoint_coordinates)

    buf = BytesIO()
    fig.savefig(buf, format='png')
    buf.seek(0)

    return HttpResponse(buf, content_type="image/png")


def get_chrom_length(plot_id, chrom):
    assembly = Plot.objects.get(id = plot_id).assembly
    return assembly.chromosomes.get(name = chrom).size


def get_region_or_err_msg(search_text, plot_id):

    search_text  = re.sub(r'(\s|,)', '', search_text)

    if search_text == '':
        return 'Enter valid position query'

    sre = re.search("^chr(\d+|X|Y):(\d+)-(\d+)$",search_text)

    if not sre:
        return '"{search_text}" is not valid position query'.format(search_text = search_text)

    sre =  sre.groups()

    chrom = 'chr' + sre[0]
    start =  int(sre[1])
    end = int(sre[2])

    if start >= end:
        return 'End coordinate should be greater than start coordinate. Your position query: {search_text}'.format(search_text = search_text)

    try:    
        chrom_size = get_chrom_length(plot_id, chrom)
       
        if end > chrom_size:
            return 'End coordinate greater than chromosome size ({chrom_size}). Your position query: {search_text}'.format(chrom_size = chrom_size, search_text = search_text)

        if start > chrom_size:
            return 'Start coordinate greater then chromosome size ({chrom_size}). Your position query: {search_text}'.format(chrom_size = chrom_size, search_text = search_text)

    except ObjectDoesNotExist:
        return  'Chromosome "{chrom}" does not exists. Search text: {search_text}'.format(chrom = chrom, search_text = search_text)

    return  chrom, start, end

def move(start, end, perc, right):
    region_len =  end - start
    m =int(region_len  * perc)

    if right:
        return start + m, end + m, 100 * perc
    else:
        return max(start - m, 0), max(end - m, region_len), 100 * perc

def zoom(start, end, perc, zoom_in):

    if  zoom_in:
        perc = 1 / perc

    region_len =  end - start
    middle = start + region_len / 2

    new_region_len  = region_len * perc

    return max(int(middle - new_region_len / 2), 0), max(int(middle + new_region_len / 2), int(new_region_len ))



def browser(request, p_id,  p_chrom = None, p_start = None, p_end = None):

    perc_move = (0.5, 0.25)
    perc_zoom = 1.25

    p_plot = Plot.objects.get(id = p_id)
    
    c_chrom, c_start, c_end, c_interval_start, c_interval_end = getPlotCookie(request, p_id)

    if p_chrom is None:
        p_chrom = c_chrom
        p_start = c_start
        p_end = c_end


    p_name_filters = sorted(p_plot.getNameFilters(p_chrom, p_start, p_end))
    name_filter = ''
    get_url = ''
    results = ''

    if request.method == 'GET': 

        search_text = request.GET.get('search_text', '')
        name_filter = request.GET.get('name_filter', '')
        interval_start = request.GET.get('interval_start', c_interval_start or '')
        interval_end = request.GET.get('interval_end', c_interval_end or '')

        p_interval_start = request.GET.get('interval_start', c_interval_start)
        p_interval_end = request.GET.get('interval_end', c_interval_end)

        setPlotCookie(request, p_id, p_chrom, p_start, p_end, p_interval_start, p_interval_end)

        region_or_err_msg = get_region_or_err_msg(search_text, p_id)

        if len(region_or_err_msg) == 3:
            p_chrom, p_start, p_end = region_or_err_msg
        elif search_text  == '':
            pass
        else:
            messages.error(request, region_or_err_msg) 

        get_url = '?' +  urlencode({'name_filter':  name_filter, 
                                    'interval_start': interval_start, 
                                    'interval_end': interval_end}, quote_via=quote_plus)


        if p_plot.hasEval() and p_interval_start is not None and p_interval_end is not None and  p_interval_start != '' and p_interval_end != '':
            results = ranking(p_plot.eval, p_chrom, p_interval_start, p_interval_end)

    else:
        pass

    return TemplateResponse(request, 'tadeus/browser.html', {'p_id': p_id, 
                           'p_plot': p_plot,
                           'p_name_filters': p_name_filters,
                           'p_cols': 1,
                           'p_chrom': p_chrom, 
                           'p_start': p_start, 
                           'p_end': p_end,
                           'name_filter': name_filter,
                           'move': ( move( p_start, p_end, perc_move[0] , False), 
                                     move( p_start, p_end, perc_move[1] , False),
                                     move( p_start, p_end, perc_move[1] , True),
                                     move( p_start, p_end, perc_move[0] , True)
                                ),
                           'zoom_in': zoom( p_start, p_end, perc_zoom, True),
                           'zoom_out': zoom( p_start, p_end, perc_zoom, False),
                           'region_len': p_end - p_start,
                           'get_url':  get_url,
                           'results': results,
                           'interval_start': interval_start,
                           'interval_end': interval_end
            })


def zoom_breakpoint(size, shift, perc, zoom_in):

    if  zoom_in:
        perc = 1 / perc

    return urlencode({'shift': int(shift * perc), 'size': int(size * perc)}, quote_via=quote_plus)    

def move_breakpoint(size, shift, perc, right):
    
    m = int(size * perc)

    if right:
        new_shift =  shift + m
    else:
        new_shift = shift - m

    return urlencode({'shift':  new_shift, 'size': size}, quote_via=quote_plus), 100 * perc 

def breakpoint_browser(request, p_id, p_breakpoint_id):

    perc_move = (0.2, 0.1)
    perc_zoom = 1.25

    breakpoint = Breakpoint.objects.get(id = p_breakpoint_id)

    p_plot = Plot.objects.get(id = p_id)

    if request.method == 'GET': 
        p_size = int(request.GET.get('size',  2000000))
        p_shift = int(request.GET.get('shift', 0))

    else:
        pass

    if 2 * abs(p_shift) < p_size:

        right_size = int(p_size / 2) - p_shift

        if breakpoint.right_inverse:
            breakpoint.right_start = breakpoint.right_coord- right_size 
            breakpoint.right_end = breakpoint.right_coord
        else:
            breakpoint.right_start = breakpoint.right_coord
            breakpoint.right_end = breakpoint.right_coord + right_size

        left_size = int(p_size / 2) + p_shift 

        if breakpoint.left_inverse:
            breakpoint.left_start = breakpoint.left_coord
            breakpoint.left_end = breakpoint.left_coord + left_size 
        else:
            breakpoint.left_start = breakpoint.left_coord - left_size
            breakpoint.left_end = breakpoint.left_coord

        breakpoint.left_width_prop = int(left_size / p_size * DEFAULT_WIDTH_PROP)
        breakpoint.right_width_prop = int(right_size / p_size * DEFAULT_WIDTH_PROP)
    
    elif p_size  <= 2 * p_shift:

        breakpoint.left_start = breakpoint.left_coord  - p_shift - p_size
        breakpoint.left_end = breakpoint.left_coord - p_shift

        breakpoint.left_width_prop = DEFAULT_WIDTH_PROP

    else:
        breakpoint.right_start =  breakpoint.right_coord - p_shift - p_size
        breakpoint.right_end = breakpoint.right_coord - p_shift
   
        breakpoint.right_width_prop = DEFAULT_WIDTH_PROP

    url_params = {}

    if breakpoint.left_start: url_params['left_start'] = breakpoint.left_start
    if breakpoint.left_end: url_params['left_end'] = breakpoint.left_end
    if breakpoint.right_start: url_params['right_start'] = breakpoint.right_start
    if breakpoint.right_end: url_params['right_end'] = breakpoint.right_end

    get_url = '?' +  urlencode(url_params, quote_via=quote_plus)

    return TemplateResponse(request, 'tadeus/browser_breakpoint.html', {'p_id': p_id, 
                           'p_plot': p_plot,
                           'p_breakpoint': breakpoint,
                           'p_size': p_size, 
                           'p_shift': p_shift, 
                           'move': ( move_breakpoint( p_size, p_shift, perc_move[0] , False), 
                                     move_breakpoint( p_size, p_shift, perc_move[1] , False),
                                     move_breakpoint( p_size, p_shift, perc_move[1] , True),
                                     move_breakpoint( p_size, p_shift, perc_move[0] , True)
                                ),
                           'zoom_in': zoom_breakpoint( p_size, p_shift, perc_zoom, True),
                           'zoom_out': zoom_breakpoint( p_size, p_shift, perc_zoom, False),
                           'get_url':  get_url
            })



def breakpoints(request):

    breakpoints = Breakpoint.objects.all()

    if request.method == 'GET': 
        min_range = request.GET.get('min_range')
        max_range = request.GET.get('max_range')
        chrom = request.GET.get('chrom')

    q_left = Q()
    q_right = Q()

    if chrom:
        q_left &= Q(left_chrom__name__iexact = chrom)
        q_right &= Q(right_chrom__name__iexact = chrom)
    if min_range:
        q_left &= Q(left_coord__gte = min_range)
        q_right &= Q(right_coord__gte = min_range)
    if max_range:
        q_left &= Q(left_coord__lte = max_range)
        q_right &= Q(right_coord__lte = max_range)

    f =  BreakpointFilter(request.GET, queryset = breakpoints.filter(q_left | q_right))
    table =  BreakpointTable(f.qs)

    RequestConfig(request).configure(table)

    samples = Sample.objects.all().order_by('name', 'id')

    return render(request, 'tadeus/breakpoints.html', {'table': table,'filter': f, 'samples': samples })