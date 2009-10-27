#-*- coding: utf-8 -*-
# Copyright (C) 2009, Luís Pedro Coelho <lpc@cmu.edu>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
#  all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
#  THE SOFTWARE.

'''
redis_store: store based on a redis backend
'''
from __future__ import division

try:
    import cPickle as pickle
except ImportError:
    import pickle

try:
    import redis
except ImportError:
    try:
        from .thirdparty import redis
    except ImportError:
        redis = None

def _resultname(name):
    return 'result:' + name
def _lockname(name):
    return 'lock:' + name
_LOCKED, _NOT_LOCKED = 0,1

class redis_store(object):
    def __init__(self, url):
        '''
        '''
        if redis is None:
            raise IOError, 'jug.redis_store: redis module is not found!'
        self.redis = redis.Redis()

    def dump(self, object, outname):
        '''
        dump(outname, object)
        '''
        s = pickle.dumps(object)
        self.redis.set(_resultname(outname), s)


    def can_load(self, name):
        '''
        can = can_load(name)
        '''
        return self.redis.exists(_resultname(name))


    def load(self, name):
        '''
        obj = load(name)

        Loads the objects. Equivalent to pickle.load(), but a bit smarter at times.
        '''
        s = self.redis.get(_resultname(name))
        return pickle.loads(str(s))


    def remove(self, name):
        '''
        was_removed = remove(name)

        Remove the entry associated with name.

        Returns whether any entry was actually removed.
        '''
        return self.redis.delete(_resultname(name))


    def cleanup(self, active):
        '''
        cleanup()

        Implement 'cleanup' command
        '''
        existing = self.redis.keys('result:*')
        for act in active:
            try:
                existing.remove(_resultname(act))
            except KeyError:
                pass
        for superflous in existing:
            self.redis.delete(_resultname(superflous))


    def getlock(self, name):
        return redis_lock(self.redis, name)


    def close(self):
        self.redis.disconnect()



class redis_lock(object):
    '''
    redis_lock

    Functions:
    ----------

        * get(): acquire the lock
        * release(): release the lock
        * is_locked(): check lock state
    '''

    def __init__(self, redis, name):
        self.name = _lockname(name)
        self.redis = redis
        # set with preserve=True is SETNX
        self.redis.set(self.name, _NOT_LOCKED, preserve=True)

    def get(self):
        '''
        lock.get()
        '''
        previous = self.redis.getset(self.name, _LOCKED)
        return previous == _NOT_LOCKED


    def release(self):
        '''
        lock.release()

        Removes lock
        '''
        self.redis.set(self.name, _NOT_LOCKED)

    def is_locked(self):
        '''
        locked = lock.is_locked()
        '''
        status = self.redis.get(self.name)
        return status is not None and status == _LOCKED

# vim: set ts=4 sts=4 sw=4 expandtab smartindent:
