#! /usr/bin/python
from modulefinder import ModuleFinder

finder = ModuleFinder()
finder.run_script('__init__.py')

print 'Loaded modules:'
for name, mod in finder.modules.iteritems():
    print '%s: ' % name,
    print ','.join(mod.globalnames.keys()[:3])

print '-'*50
print 'Modules not imported:'
print '\n'.join(finder.badmodules.iterkeys())
