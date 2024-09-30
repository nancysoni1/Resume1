from django.shortcuts import render,redirect
from django.contrib.auth.models import auth,User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
import requests
from bs4 import BeautifulSoup as bs
import re# used to search, replace, or validate string patterns, often used to filter specific data from the HTML content.
#now we will define a function which retrieve all the details using api , apis me model/database ki jroorat nhi ,i will make a function that lists user recently played artists
# we will use track_id and track_nam eto get track_image we will get the url from url at top(we will go to spotify and then check) after  clicking on any track
def get_track_image(track_id,track_name):
    url = 'https://open.spotify.com/track/'+track_id
    r = requests.get(url)
    soup = bs(r.content)#r.content mean us url se jo content aaya,BeautifulSoup processes this HTML to create a parse tree that you can then navigate to extract specific data(data trees me divide values alag expressions alag)
    image_links_html = soup.find('img',{'alt':track_name})
    #search for the first <img> tag in the HTML that has an alt attribute matching the value of track_name.
    if image_links_html:
        image_links = image_links_html['srcset']
        #srcset attribute is commonly used to provide multiple versions of an image to allow the browser to choose the most appropriate one based on the display characteristics
    else:
        image_links = ''
    match = re.search(r'https:\/\/i\.scdn\.co\/image\/[^\s,]+', image_links)
    #is using a regular expression (regex) to search for a specific URL pattern within the image_links string
    #'r'...': The r before the string indicates that it's a raw string, meaning that backslashes (\) are treated as literal characters, not as escape sequences https://i.scdn.co/image/   ye sara process apan wahi krwa rhe jo spotify krti h so ye data apan directly waha se extract
    if match:
        # if match found match.group() will contain that url and below line basically removes the last 640w
        url_640w = match.group()
        if url_640w.endswith('640w'):
          url_640w = url_640w[:-4]  # Removes '640w' from the end of the URL

        print(url_640w)

    else:
        url_640w=''
    return url_640w

def profile(request,pk):
    url = "https://spotify-scraper.p.rapidapi.com/v1/artist/overview"

    querystring = {"artistId":"6eUKZXaKkcviH0Ku9w2n3V"}

    headers = {
	"x-rapidapi-key": "a611c51f74msh3096a98a068bf65p19fe2ajsn28c9e34d733c",
	"x-rapidapi-host": "spotify-scraper.p.rapidapi.com"
}

    response = requests.get(url, headers=headers, params=querystring)
    response_data= response.json()
    name = response_data["name"] 
    monthly_listeners = response_data["stats"]["monthlyListeners"]
    header_url = response_data["visuals"]["header"][0]["url"]
    top_tracks = []
    for track in response_data["discography"]["topTracks"]:
        trackid = track["id"]
        trackname = track["name"]
        trackimage = get_track_image(trackid,trackname)
        track_info = {
        "id":track["id"],
        "name":track["name"],
        "durationText":track["durationText"],
        "playCount":track["playCount"],
        "track_image":trackimage,
        }
        top_tracks.append(track_info)

    artist_data = {
        "name":name,
        "monthlyListeners":monthly_listeners,
        "headerURL":header_url,
        "topTracks":top_tracks,

    }
    return render(request,'profile.html',artist_data)

def search(request):
    if request.method == 'POST':
        search_query = request.POST['search_query']
        url = "https://spotify-scraper.p.rapidapi.com/v1/search"

        querystring = {"term":"search_query","type":"track"}

        headers = {
	"x-rapidapi-key": "a611c51f74msh3096a98a068bf65p19fe2ajsn28c9e34d733c",
	"x-rapidapi-host": "spotify-scraper.p.rapidapi.com"
}

        response = requests.get(url, headers=headers, params=querystring)
        track_list=[]
        data= response.json()
        search_results_count = data["tracks"]["totalCount"]
        tracks = data["tracks"]["items"]
        for track in tracks:
                track_name = track["name"]
                artist_name = track["artists"][0]["name"]
                duration = track["durationText"]
                trackid = track["id"]

                if get_track_image(trackid, track_name):
                    track_image = get_track_image(trackid, track_name)
                else:
                    track_image = "https://imgv3.fotor.com/images/blog-richtext-image/music-of-the-spheres-album-cover.jpg"

                track_list.append({
                    'track_name': track_name,
                    'artist_name': artist_name,
                    'duration': duration,
                    'trackid': trackid,
                    'track_image': track_image,
                })
        context = {
            'search_results_count': search_results_count,
            'track_list': track_list,
        }

        return render(request, 'search.html', context)
    else:
        return render(request, 'search.html')



def recently_played_artists(request):
  url = "https://spotify-scraper.p.rapidapi.com/v1/user/artists"

  querystring = {"userId":"1110908538"}

  headers = {
	"x-rapidapi-key": "a611c51f74msh3096a98a068bf65p19fe2ajsn28c9e34d733c",
	"x-rapidapi-host": "spotify-scraper.p.rapidapi.com"
}
  

  response = requests.get(url, headers=headers, params=querystring)
  response_data=response.json()
  artists_info = []
  if 'artists' in response_data:
    # letss say we want only first 20 data so new_data = data['artists'][:20] for artsist in new_data
    for artist in response_data['artists']: 
        name= artist.get('name','No Name')
        avatar_url=artist.get('visuals',{}).get('avatar',[{}])[0].get('url','NO URL')
        artist_id=artist.get('id','No ID')
        artists_info.append((name,avatar_url,artist_id))        
  return artists_info


def playlist_tracks(request):
    url = "https://spotify-scraper.p.rapidapi.com/v1/playlist/contents"
    querystring = {"playlistId": "5782GLkrpvN8zbJQRjMaSW"}
    headers = {
        "x-rapidapi-key": "a611c51f74msh3096a98a068bf65p19fe2ajsn28c9e34d733c",
        "x-rapidapi-host": "spotify-scraper.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers, params=querystring)
    response_data = response.json()

    tracks_info = []

    if 'contents' in response_data and 'items' in response_data['contents']:
        for item in response_data['contents']['items']:
            # i it necessary to write this  item.get('name', 'No name')? cant we do item['name'] ? whats the difference and if more complex  can we do ['a']['b']['c']['d'] and avatar_url=artist.get('visuals',{}).get('avatar',[{}])[0].get('url','NO URL')how three of them are different ?

            #both of them are correct the only diffence is if directly access using [][][] agar kahi koi key nhi mili toh it will raise error but in get we paas a default value
            track_name = item.get('name', 'No name')
            track_id = item.get('id', 'No ID')
            track_url = item.get('shareUrl', 'NO URL')
            duration = item.get('durationText', 'Unknown duration')
            play_count = item.get('playCount', 0)
            track_image=item.get('album',{}).get('cover',[{}])[1].get('url','NO URL')

            # Extract artist information
            artists = item.get('artists', [])
            artist_info = []
            for artist in artists:
                artist_name = artist.get('name', 'No name')
                artist_id = artist.get('id', 'No ID')
                artist_url = artist.get('shareUrl', 'NO URL')
                artist_info.append((artist_name, artist_id, artist_url))
                
# analyse the differnce in passing .1 or .track_id 
            tracks_info.append({
                'track_name': track_name,
                'track_id': track_id,
                'track_url': track_url,
                'duration': duration,
                'track_image':track_image,
                'play_count': play_count,
                'artists': artist_info
            })
    return tracks_info

def music(request,pk):
    track_id=pk
    url = "https://spotify-scraper.p.rapidapi.com/v1/playlist/metadata"

    querystring = {"track_id": track_id}

    headers = {
	"x-rapidapi-key": "a611c51f74msh3096a98a068bf65p19fe2ajsn28c9e34d733c",
	"x-rapidapi-host": "spotify-scraper.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers, params=querystring)

    data = response.json()
    track_name= data.get('name')
    owner_data=data.get('owner',{})
    artist_name = owner_data.get('name', 'No name')
    audio_details_query = track_name+artist_name
    audio_details = get_audio_details(audio_details_query)
    audio_url = audio_details[0]
    duration_text = audio_details[1]
    track_image = get_track_image(track_id,track_name)
    context = {
            'track_name':track_name,
            'artist_name':artist_name,
            'audio_url':audio_url,
            'duration_text':duration_text,
            'track_image':track_image,
            }
    
    return render(request,'music.html',context)
# this get_audio -DETAILS WE WILL PAAS IN music function access the query there then paas that in the context there using audio_details[0] and audio_details[1]
def get_audio_details(query):
    url = "https://spotify-scraper.p.rapidapi.com/v1/track/download"

    querystring = {"track":query}

    headers = {
	"x-rapidapi-key": "a611c51f74msh3096a98a068bf65p19fe2ajsn28c9e34d733c",
	"x-rapidapi-host": "spotify-scraper.p.rapidapi.com"
}

    response = requests.get(url, headers=headers, params=querystring)
    response_data=response.json()
    #response data is a dict .get  gets the value of a key, list  me .append,set me .add
    audio_details=[]
    if 'youtubeVideo' in response_data and 'audio' in response_data['youtubeVideo']:
        audio_list = response_data['youtubeVideo']['audio']
        if audio_list:
            first_audio_url = audio_list[0]['url']
            duration_text = audio_list[0]['durationText']
            audio_details.append(first_audio_url)
            audio_details.append( duration_text)
        else:
            print("no audio data available ")
    else:
        print('No youtube video or audio key found')
    return audio_details




@login_required(login_url='login')
def index(request):
    artists_info=recently_played_artists(request)
    tracks_info=playlist_tracks(request)
    context={'artists_info':artists_info,'tracks_info':tracks_info}
    # its okay function toh define krdiya but try to extract just songs as we will further use it next function where ww will take each song with id
    # yaha par aapan context me seedha functionn ki return value ko paas krwa diya therefore in this case we use index to access data but agar apan ne index function mein kuch define krke context me paas kiya hota toh in that case apan .name(poorane projects mein dekh lena) likhte otherwise in above case .0
    return render(request,'index.html',context)




def login(request):
    if request.method =='POST':
        username = request.POST['username']
        password = request.POST['password']
        user = auth.authenticate(username=username, password=password)
        if user is not None:
            auth.login(request,user)
            return redirect('/')
        else:
            messages.info(request,'Credentials invalid')
            return redirect('/login')
    
    return render(request,'login.html')



def signup(request):
     if request.method == 'POST':
        email = request.POST['email']
        username = request.POST['username']
        password = request.POST['password']
        password2 = request.POST['password2']

        if password == password2:
            if User.objects.filter(email=email).exists():
                messages.info(request, 'Email Taken')
                return redirect('signup')
            elif User.objects.filter(username=username).exists():
                messages.info(request, 'Username Taken')
                return redirect('signup')
            else:
                user = User.objects.create_user(username=username, email=email, password=password)
                user.save()

                # log user in 
                user_login = auth.authenticate(username=username, password=password)
                auth.login(request, user_login)
                return redirect('/')
        else:
            messages.info(request, 'Password Not Matching')
            return redirect('signup')
     else:    
        return render(request, 'signup.html')

@login_required(login_url='login')# we use login_required when we dont want user to use home page until and unless he is logged in
def logout(request):
    auth.logout(request)
    return redirect('login')


'''def top_artists(request):

   response = requests.get(url, headers=headers, params=querystring)
   response_data=response.json()
   # now we will make a lsit that will store all of the data of artists we will be needing artist name and id to redirect to its respective page, we will check if artist data is there in response data
  
   artists_info = []
   if 'artists' in response_data:
       for artist in response_data['artists']:
           # for every artist we will get its name and id,we will try to get the name but agar nhi mila toh it will return no name , {} blank means agar vo user nhih it will return blank dictionary, url ka address h visuals->avatar->url 
           name= artist.get('name','No Name')
           avatar_url=artist.get('visuals',{}).get('avatar',[{}])[0].get('url','NO URL')
           artist_id=artist.get('id','No ID')
           artists_info.append((name,avatar_url,artist_id))'''