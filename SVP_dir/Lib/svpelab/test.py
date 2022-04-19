

cols = list(range(len(self.data)))
if len(cols) > 0:
    f = open(filename, 'w')
    f.write('%s\n' % ', '.join(map(str, self.points)))
    for i in range(len(self.data[0])):
        d = []
        for j in cols:
            # self.ts.log_debug('data = %s' % self.data)
            # self.ts.log_debug('point names = %s' % self.points)
            # self.ts.log_debug('len(points) = %s, len(data) = %s' % (len(self.points), len(self.data)))
            # self.ts.log_debug('j = %s, i = %i, self.data[j][i] = %s' % (j, i, self.data[j][i]))
            d.append(self.data[j][i])
        f.write('%s\n' % ', '.join(map(str, d)))
    f.close()