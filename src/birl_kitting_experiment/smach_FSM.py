import smach
from geometry_msgs.msg import (
    Pose,
    Quaternion,
)
import copy
import random
from tf.transformations import (
    translation_matrix,
    quaternion_matrix,
)
import baxter_interface
import numpy
import os
from sklearn.externals import joblib

dir_of_this_script = os.path.dirname(os.path.realpath(__file__))
dmp_model_dir = os.path.join(dir_of_this_script, '..', '..', 'data', 'dmp_models')

pick_hover_height = 0.10
place_step_size = 0.07
place_hover_height = 0.10

class MoveToHomePose(smach.State):
    def __init__(self):
        smach.State.__init__(self, outcomes=['Successful'])
        self.state_no = 1 # Skill tag
        self.depend_on_prev_state = False # Set this flag accordingly

    def get_dmp_model(self):
        return joblib.load(os.path.join(dmp_model_dir, 'pre_place_to_home')) 

    def get_pose_goal(self): # Goal getter, will be reused in executing recovery policy
        home_pose = Pose()
        home_pose.position.x = 0.807696880366
        home_pose.position.y = -0.357654593225
        home_pose.position.z = 0.485923232894
        home_pose.orientation = Quaternion(
            x= 0.0360998886755,
            y= 0.987682209702,
            z= -0.0220824712831,
            w= 0.150642009872,
        )

        return home_pose

    def determine_successor(self): # Determine next state
        return 'Successful'

class DeterminePickPose(smach.State):
    pick_pose = None
    already_pick_count = 0
    def __init__(self):
        smach.State.__init__(self, outcomes=['GotOneFromVision', 'VisionSaysNone'])
        self.state_no = 2 # Skill tag
        self.depend_on_prev_state = False # Set this flag accordingly

    def determine_successor(self): # Determine next state
        if DeterminePickPose.already_pick_count >= 3:
            return 'VisionSaysNone'
        

        DeterminePickPose.pick_pose = Pose()
        DeterminePickPose.pick_pose.position.x = 0.71911746461+random.uniform(-0.1, +0.1)
        DeterminePickPose.pick_pose.position.y = -0.134129746892+random.uniform(-0.1, +0.1)
        DeterminePickPose.pick_pose.position.z = 0.315673091393+random.uniform(-0.1, +0.1)
        DeterminePickPose.pick_pose.orientation = Quaternion(
            x= -0.25322831688,
            y= 0.966477494136,
            z= 0.0131814413255,
            w= -0.0402855118249,
        )
        DeterminePickPose.already_pick_count += 1
        return 'GotOneFromVision'

class MoveToPrePickPoseWithEmptyHand(smach.State):
    def __init__(self):
        smach.State.__init__(self, outcomes=['Successful'])
        self.state_no = 3 # Skill tag
        self.depend_on_prev_state = True # Set this flag accordingly

    def get_dmp_model(self):
        return joblib.load(os.path.join(dmp_model_dir, 'home_to_pre_pick')) 
    
    def get_pose_goal(self):
        pose = copy.deepcopy(DeterminePickPose.pick_pose)
        pos = pose.position
        ori = pose.orientation
        base_to_pose_mat = numpy.dot(translation_matrix((pos.x, pos.y, pos.z)), quaternion_matrix((ori.x, ori.y, ori.z, ori.w)))
        pose.position.x -= pick_hover_height*base_to_pose_mat[0, 2]
        pose.position.y -= pick_hover_height*base_to_pose_mat[1, 2]
        pose.position.z -= pick_hover_height*base_to_pose_mat[2, 2]
        return pose

    def determine_successor(self): # Determine next state
        return 'Successful'

class Pick(smach.State):
    def __init__(self):
        smach.State.__init__(self, outcomes=['Successful'])
        self.state_no = 4 # Skill tag
        self.depend_on_prev_state = True # Set this flag accordingly

    def before_motion(self):
        baxter_interface.Gripper('right').open()

    def after_motion(self):
        baxter_interface.Gripper('right').close()
    
    def get_pose_goal(self):
        pose = copy.deepcopy(DeterminePickPose.pick_pose)
        return pose

    def determine_successor(self): # Determine next state
        return 'Successful'

class MoveToPrePickPoseWithFullHand(smach.State):
    def __init__(self):
        smach.State.__init__(self, outcomes=['Successful'])
        self.state_no = 5 # Skill tag
        self.depend_on_prev_state = True # Set this flag accordingly
    
    def get_pose_goal(self):
        pose = copy.deepcopy(DeterminePickPose.pick_pose)
        pos = pose.position
        ori = pose.orientation
        base_to_pose_mat = numpy.dot(translation_matrix((pos.x, pos.y, pos.z)), quaternion_matrix((ori.x, ori.y, ori.z, ori.w)))
        pose.position.x -= pick_hover_height*base_to_pose_mat[0, 2]
        pose.position.y -= pick_hover_height*base_to_pose_mat[1, 2]
        pose.position.z -= pick_hover_height*base_to_pose_mat[2, 2]
        return pose

    def determine_successor(self): # Determine next state
        return 'Successful'

class DeterminePlacePose(smach.State):
    place_pose = None
    already_plac_count = 0
    def __init__(self):
        smach.State.__init__(self, outcomes=['Successful'])
        self.state_no = 6 # Skill tag
        self.depend_on_prev_state = False # Set this flag accordingly

    def determine_successor(self): # Determine next state
        DeterminePlacePose.place_pose = Pose()
        DeterminePlacePose.place_pose.position.x = 0.0689814878187
        DeterminePlacePose.place_pose.position.y = -0.809844772878
        DeterminePlacePose.place_pose.position.z = 0.110868228768
        DeterminePlacePose.place_pose.orientation = Quaternion(
            x= 0.00602278560434,
            y= 0.999630513296,
            z= -0.0262524593887,
            w= 0.00365668116077,
        )

        pos = DeterminePlacePose.place_pose.position
        ori = DeterminePlacePose.place_pose.orientation
        base_to_place_mat = numpy.dot(translation_matrix((pos.x, pos.y, pos.z)), quaternion_matrix((ori.x, ori.y, ori.z, ori.w)))

        step = DeterminePlacePose.already_plac_count*place_step_size

        DeterminePlacePose.place_pose.position.x -= step*base_to_place_mat[0, 0]
        DeterminePlacePose.place_pose.position.y -= step*base_to_place_mat[1, 0]
        DeterminePlacePose.place_pose.position.z -= step*base_to_place_mat[2, 0]

        DeterminePlacePose.already_plac_count += 1
        return 'Successful'

class MoveToPrePlacePoseWithFullHand(smach.State):
    def __init__(self):
        smach.State.__init__(self, outcomes=['Successful'])
        self.state_no = 7 # Skill tag
        self.depend_on_prev_state = True # Set this flag accordingly

    def get_dmp_model(self):
        return joblib.load(os.path.join(dmp_model_dir, 'pre_pick_to_pre_place')) 
    
    def get_pose_goal(self):
        pose = copy.deepcopy(DeterminePlacePose.place_pose)
        pos = pose.position
        ori = pose.orientation
        base_to_pose_mat = numpy.dot(translation_matrix((pos.x, pos.y, pos.z)), quaternion_matrix((ori.x, ori.y, ori.z, ori.w)))
        pose.position.x -= place_hover_height*base_to_pose_mat[0, 2]
        pose.position.y -= place_hover_height*base_to_pose_mat[1, 2]
        pose.position.z -= place_hover_height*base_to_pose_mat[2, 2]
        return pose

    def determine_successor(self): # Determine next state
        return 'Successful'

class Place(smach.State):
    def __init__(self):
        smach.State.__init__(self, outcomes=['Successful'])
        self.state_no = 8 # Skill tag
        self.depend_on_prev_state = True # Set this flag accordingly

    def after_motion(self):
        baxter_interface.Gripper('right').open()
    
    def get_pose_goal(self):
        pose = copy.deepcopy(DeterminePlacePose.place_pose)
        return pose

    def determine_successor(self): # Determine next state
        return 'Successful'

class MoveToPrePlacePoseWithEmptyHand(smach.State):
    def __init__(self):
        smach.State.__init__(self, outcomes=['Successful'])
        self.state_no = 9 # Skill tag
        self.depend_on_prev_state = True # Set this flag accordingly
    
    def get_pose_goal(self):
        pose = copy.deepcopy(DeterminePlacePose.place_pose)
        pos = pose.position
        ori = pose.orientation
        base_to_pose_mat = numpy.dot(translation_matrix((pos.x, pos.y, pos.z)), quaternion_matrix((ori.x, ori.y, ori.z, ori.w)))
        pose.position.x -= place_hover_height*base_to_pose_mat[0, 2]
        pose.position.y -= place_hover_height*base_to_pose_mat[1, 2]
        pose.position.z -= place_hover_height*base_to_pose_mat[2, 2]
        return pose

    def determine_successor(self): # Determine next state
        return 'Successful'

def assembly_user_defined_sm():
    sm = smach.StateMachine(outcomes=['TaskFailed', 'TaskSuccessful'])
    with sm:
        smach.StateMachine.add(
            MoveToHomePose.__name__,
            MoveToHomePose(),
            transitions={
                'Successful': DeterminePickPose.__name__
            }
        )
        smach.StateMachine.add(
            DeterminePickPose.__name__,
            DeterminePickPose(),
            transitions={
                'GotOneFromVision': MoveToPrePickPoseWithEmptyHand.__name__,
                'VisionSaysNone': 'TaskSuccessful',
            }
        )
        smach.StateMachine.add(
            MoveToPrePickPoseWithEmptyHand.__name__,
            MoveToPrePickPoseWithEmptyHand(),
            transitions={
                'Successful': Pick.__name__
            }
        )
        smach.StateMachine.add(
            Pick.__name__,
            Pick(),
            transitions={
                'Successful': MoveToPrePickPoseWithFullHand.__name__
            }
        )
        smach.StateMachine.add(
            MoveToPrePickPoseWithFullHand.__name__,
            MoveToPrePickPoseWithFullHand(),
            transitions={
                'Successful': DeterminePlacePose.__name__
            }
        )
        smach.StateMachine.add(
            DeterminePlacePose.__name__,
            DeterminePlacePose(),
            transitions={
                'Successful': MoveToPrePlacePoseWithFullHand.__name__
            }
        )
        smach.StateMachine.add(
            MoveToPrePlacePoseWithFullHand.__name__,
            MoveToPrePlacePoseWithFullHand(),
            transitions={
                'Successful': Place.__name__
            }
        )
        smach.StateMachine.add(
            Place.__name__,
            Place(),
            transitions={
                'Successful': MoveToPrePlacePoseWithEmptyHand.__name__
            }
        )
        smach.StateMachine.add(
            MoveToPrePlacePoseWithEmptyHand.__name__,
            MoveToPrePlacePoseWithEmptyHand(),
            transitions={
                'Successful': MoveToHomePose.__name__
            }
        )
    return sm
