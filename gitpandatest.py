from gitpandas import Repository
import numpy as np
import lifelines
import matplotlib.pyplot as plt

threshold = 20
repo = Repository(working_dir='git://github.com/ogr3/race-management-system.git', verbose=True)
fch = repo.file_change_history(limit=100000, extensions=['py', 'pyx', 'h', 'c', 'cpp', 'java', 'xml'])
fch['file_owner'] = ''
fch['refactor'] = 0
fch['timestamp'] = fch.index.astype(np.int64) // (24 * 3600 * 10**9)
fch['observed'] = False
fch = fch.reindex()
fch = fch.reset_index()

# add in the file owner and whether or not each item is a refactor
for idx, row in fch.iterrows():
    fch.set_value(idx, 'file_owner', repo.file_owner(row.rev, row.filename, committer=True))
    if abs(row.insertions - row.deletions) > threshold:
        fch.set_value(idx, 'refactor', 1)
    else:
        fch.set_value(idx, 'refactor', 0)

# add in the time since column
fch['time_until_refactor'] = 0
for idx, row in fch.iterrows():
    ts = None
    chunk = fch[(fch['timestamp'] > row.timestamp) & (fch['refactor'] == 1) & (fch['filename'] == row.filename)]
    if chunk.shape[0] > 0:
        ts = chunk['timestamp'].min()
        fch.set_value(idx, 'observed', True)
    else:
        ts = fch['timestamp'].max()
    fch.set_value(idx, 'time_until_refactor', ts - row.timestamp)

# plot out some survival curves
fig = plt.figure()
ax = plt.subplot(111)
for filename in set(fch['file_owner'].values):
    sample = fch[fch['file_owner'] == filename]
    if sample.shape[0] > 20:
        print('Evaluating %s' % (filename, ))
        kmf = lifelines.KaplanMeierFitter()
        kmf.fit(sample['time_until_refactor'].values, event_observed=sample['observed'], timeline=list(range(365)), label=filename)
        ax = kmf.survival_function_.plot(ax=ax)

plt.title('Survival function of file owners (thres=%s)' % (threshold, ))
plt.xlabel('Lifetime (days)')
#plt.show()
plt.savefig('example', dpi=None, facecolor='w', edgecolor='w',
            orientation='portrait', papertype=None, format=None,
            transparent=False, bbox_inches=None, pad_inches=0.1,
            frameon=None)
