"""
This is the basis of the typeclass system. 

The idea is have the object as a normal class with the
database-connection tied to itself through a property.

The instances of all the different object types are all tied to their
own database object stored in the 'dbobj' property.  All attribute
get/set operations are channeled transparently to the database object
as desired. You should normally never have to worry about the database
abstraction, just do everything on the TypeClass object.

That an object is controlled by a player/user is just defined by its
'user' property being set.  This means a user may switch which object
they control by simply linking to a new object's user property.
"""

from src.typeclasses.typeclass import TypeClass
from src.objects.exithandler import EXITHANDLER


#
# Base class to inherit from. 
#

class Object(TypeClass):
    """
    This is the base class for all in-game objects.
    Inherit from this to create different types of
    objects in the game. 
    """    

    def __eq__(self, other):
        """
        This has be located at this level, having it in the
        parent doesn't work.
        """
        
        result = other and other.id == self.id
        try:
            uresult = other and (other.user.id == self.user.id) 
        except AttributeError:
            uresult = False 
        return result or uresult 

    # hooks called by the game engine

    def basetype_setup(self):
        """
        This sets up the default properties of an Object,
        just before the more general at_object_creation.
        """
        # the default security setup fallback for a generic
        # object. Overload in child for a custom setup. Also creation
        # commands may set this (create an item and you should be its
        # controller, for example)

        dbref = self.dbobj.dbref

        self.locks.add("control:id(%s) or perm(Immortals)" % dbref)  # edit locks/permissions, delete
        self.locks.add("examine:perm(Builders)")  # examine properties 
        self.locks.add("edit:perm(Wizards)")   # edit properties/attributes 
        self.locks.add("delete:perm(Wizards)") # delete object 
        self.locks.add("get:all()")   # pick up object
        self.locks.add("call:true()") # allow to call commands on this object

    def at_object_creation(self):
        """
        Called once, when this object is first
        created. 
        """ 
        pass

    def at_first_login(self):
        """
        Only called once, the very first
        time the user logs in.
        """
        pass
    def at_pre_login(self):
        """
        Called every time the user logs in,
        before they are actually logged in.
        """
        pass
    def at_post_login(self):
        """
        Called at the end of the login
        process, just before letting
        them loose. 
        """
        pass

    def at_disconnect(self):
        """
        Called just before user
        is disconnected.
        """
        pass

    # hooks called when moving the object

    def at_before_move(self, destination):
        """
        Called just before starting to move
        this object to destination. 

        destination - the object we are moving to

        If this method returns False/None, the move
        is cancelled before it is even started. 
        """
        #return has_perm(self, destination, "can_move")
        return True 

    def announce_move_from(self, destination):
        """
        Called if the move is to be announced. This is
        called while we are still standing in the old
        location. 

        destination - the place we are going to. 
        """
        if not self.location:
            return 
        name = self.name 
        loc_name = ""
        loc_name = self.location.name 
        dest_name = destination.name
        string = "%s is leaving %s, heading for %s."
        self.location.msg_contents(string % (name, loc_name, dest_name), exclude=self)
        
    def announce_move_to(self, source_location):
        """
        Called after the move if the move was not quiet. At this
        point we are standing in the new location. 

        source_location - the place we came from 
        """

        name = self.name        
        if not source_location and self.location.has_player:
            # This was created from nowhere and added to a player's
            # inventory; it's probably the result of a create command.
            string = "You now have %s in your possession." % name
            self.location.msg(string)
            return 

        src_name = "nowhere"
        loc_name = self.location.name
        if source_location:
            src_name = source_location.name
        string = "%s arrives to %s from %s." 
        self.location.msg_contents(string % (name, loc_name, src_name), exclude=self)


    def at_after_move(self, source_location):
        """
        Called after move has completed, regardless of quiet mode or not. 
        Allows changes to the object due to the location it is now in.

        source_location - where we came from 
        """
        pass


    def at_object_leave(self, moved_obj, target_location):
        """
        Called just before an object leaves from inside this object

        moved_obj - the object leaving
        target_location - where the object is going.
        """
        pass

    def at_object_receive(self, moved_obj, source_location):
        """
        Called after an object has been moved into this object. 

        moved_obj - the object moved into this one
        source_location - where moved_object came from. 
        """
        pass
        

    # hooks called by the default cmdset. 
    
    def return_appearance(self, pobject):
        """
        This is a convenient hook for a 'look'
        command to call. 
        """
        if not pobject:
            return 
        string = "{c%s{n" % self.name
        desc = self.attr("desc")
        if desc:
            string += "\n %s" % desc
        exits = [] 
        users = []
        things = []
        for content in self.contents:
            if content == pobject:
                continue 
            name = content.name
            if content.destination:
                exits.append(name)
            elif content.has_player:
                users.append(name)
            else:
                things.append(name)
        if exits:
            string += "\n{wExits:{n " + ", ".join(exits)
        if users or things:
            string += "\n{wYou see: {n"
            if users: 
                string += "{c" + ", ".join(users) + "{n "
            if things: 
                string += ", ".join(things)            
        return string

    def at_msg_receive(self, msg, from_obj=None, data=None):
        """
        This hook is called whenever someone 
        sends a message to this object.

        Note that from_obj may be None if the sender did
        not include itself as an argument to the obj.msg()
        call - so you have to check for this. . 
  
        Consider this a pre-processing method before
        msg is passed on to the user sesssion. If this 
        method returns False, the msg will not be 
        passed on.

        msg = the message received
        from_obj = the one sending the message
        """
        return True 

    def at_msg_send(self, msg, to_obj=None, data=None):
        """
        This is a hook that is called when /this/ object
        sends a message to another object with obj.msg()
        while also specifying that it is the one sending. 
   
        Note that this method is executed on the object
        passed along with the msg() function (i.e. using
        obj.msg(msg, caller) will then launch caller.at_msg())
        and if no object was passed, it will never be called.         
        """
        pass
        
    def at_desc(self, looker=None):
        """
        This is called whenever someone looks
        at this object. Looker is the looking
        object. 
        """
        pass
    
    def at_object_delete(self):
        """
        Called just before the database object is
        permanently delete()d from the database. If
        this method returns False, deletion is aborted. 
        """
        return True

    def at_get(self, getter):
        """
        Called when this object has been picked up. Obs-
        this method cannot stop the pickup - use permissions
        for that!

        getter - the object getting this object.
        """
        pass

    def at_drop(self, dropper):
        """
        Called when this object has been dropped.

        dropper - the object which just dropped this object.
        """
        pass
    def at_say(self, speaker, message):
        """
        Called on this object if an object inside this object speaks.
        The string returned from this method is the final form 
        of the speech. Obs - you don't have to add things like 
        'you say: ' or similar, that is handled by the say command.

        speaker - the object speaking
        message - the words spoken.
        """
        return message

#
# Base Player object 
#

class Character(Object):
    """
    This is just like the Object except it implements its own
    version of the at_object_creation to set up the script
    that adds the default cmdset to the object.
    """    

    def basetype_setup(self):
        """
        Setup character-specific security
        """
        super(Character, self).basetype_setup()
        self.locks.add("puppet:id(%s) or perm(Immortals)" % self.dbobj.dbref) # who may become this object's player
        self.locks.add("get:false()") # noone can pick up the character
        self.locks.add("call:false()") # no commands can be called on character        

        # add the default cmdset
        from settings import CMDSET_DEFAULT        
        self.cmdset.add_default(CMDSET_DEFAULT, permanent=True)
        # no other character should be able to call commands on the Character. 
        self.cmdset.outside_access = False 

    def at_object_creation(self):
        """
        All this does (for now) is to add the default cmdset. Since
        the script is permanently stored to this object (the permanent
        keyword creates a script to do this), we should never need to
        do this again for as long as this object exists.
        pass
        """        
        
    def at_after_move(self, source_location):
        "Default is to look around after a move."
        self.execute_cmd('look')
            
#
# Base Room object 
#

class Room(Object):
    """
    This is the base room object. It's basically
    like any Object except its location is None.
    """
    def basetype_setup(self):
        """
        Simple setup, shown as an example
        (since default is None anyway)
        """

        super(Room, self).basetype_setup()
        self.locks.add("get:false()")        

        super(Room, self).basetype_setup()
        self.location = None 

class Exit(Object):
    """
    This is the base exit object - it connects a location
    to another. What separates it from other objects
    is that it has the 'destination' property defined.    
    Note that property is the only identifier to
    separate an exit from normal objects, so if the property
    is removed, it will be treated like any other object. This
    also means that any object can be made an exit by setting
    the property destination to a valid location
    ('Quack like a duck...' and so forth).
    """        
    def basetype_setup(self):
        """
        Setup exit-security
        """
        # the lock is open to all by default
        super(Exit, self).basetype_setup()
        self.locks.add("traverse:all()") # who can pass through exit
        self.locks.add("get:false()")    # noone can pick up the exit 

    def at_object_creation(self):
        """
        An example just for show; the destination property
        is usually set at creation time, not as part of the class
        definition (unless you want an entire class of exits
        all leadning to the same hard-coded place ...)
        """
        # having destination != None is what makes it an exit 
        # (what's set here won't last)
        if self.location:
            self.destination = self.location
        else:
            self.destination = 2 # use limbo as a failsafe
        
    def at_object_delete(self):
        """
        We have to make sure to clean the exithandler cache
        when deleting the exit, or a new exit could be created
        out of sync with the cache. You should do this also if
        overloading this function in a child class. 
        """
        EXITHANDLER.clear(self.dbobj)
        return True 
