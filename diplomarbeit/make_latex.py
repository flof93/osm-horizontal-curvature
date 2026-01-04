from pathlib import Path
import contextily as cx



DATA_DICT = Path('./data/')
STADIA_API = 'ccf6fac2-c284-43e8-b9f2-83716f034ba2'



ax=df_vie.plot(color='r')
ax=df_vie.plot(cmap='gist_rainbow', figsize=(10,10))
fig=ax.get_figure()
ax.set_axis_off()
#cx.add_basemap(ax=ax, crs=df_vie.crs, source=cx.providers.TopPlusOpen.Grey)

provider = cx.providers.Stadia.AlidadeSmooth(api_key=STADIA_API)
provider["url"] = provider["url"] + "?api_key={api_key}"
cx.add_basemap(ax, crs=df_vie.crs, source=provider)

fig.savefig('./temp/wien.png', bbox_inches='tight', pad_inches=0.2)