import os

from ament_index_python.packages import get_package_share_directory


from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration

from launch_ros.actions import Node



def generate_launch_description():


    # Include the robot_state_publisher launch file, provided by our own package. Force sim time to be enabled
    # !!! MAKE SURE YOU SET THE PACKAGE NAME CORRECTLY !!!

    package_name='articubot_one' #<--- CHANGE ME

    rsp = IncludeLaunchDescription(
                PythonLaunchDescriptionSource([os.path.join(
                    get_package_share_directory(package_name),'launch','rsp.launch.py'
                )]), launch_arguments={'use_sim_time': 'false', 'use_ros2_control': 'false'}.items()
    )

    # world = LaunchConfiguration('world')

    # world_arg = DeclareLaunchArgument(
    #     'world',
    #     default_value="empty.sdf",
    #     description='World to load'
    #     )

    joystick = IncludeLaunchDescription(
                PythonLaunchDescriptionSource([os.path.join(
                    get_package_share_directory(package_name),'launch','joystick.launch.py'
                )]), launch_arguments={'use_sim_time': 'true'}.items()
    )

    twist_mux_params = os.path.join(get_package_share_directory(package_name),'config','twist_mux.yaml')
    twist_mux = Node(
            package="twist_mux",
            executable="twist_mux",
            parameters=[twist_mux_params, {'use_sim_time': True}],
            remappings=[('/cmd_vel_out','/cmd_vel_unstamped')]
        )

    # Gazebo (gz-sim / Harmonic) publishes unstamped Twist internally on the plugin's
    # topic, but the ros_gz_bridge config expects a stamped Twist on /cmd_vel
    twist_stamper = Node(
            package='twist_stamper',
            executable='twist_stamper',
            parameters=[{'use_sim_time': True}],
            remappings=[('/cmd_vel_in','/cmd_vel_unstamped'),
                        ('/cmd_vel_out','/cmd_vel')]
         )

    world_file = os.path.join(get_package_share_directory(package_name),'worlds','empty.world')

    # Launch Gazebo (gz sim / Harmonic), provided by the ros_gz_sim package
    gazebo = IncludeLaunchDescription(
                PythonLaunchDescriptionSource([os.path.join(
                    get_package_share_directory('ros_gz_sim'), 'launch', 'gz_sim.launch.py')]),
                    launch_arguments={'gz_args': f'-r -s {world_file}'}.items()
             )

    # Spawn the robot into gz sim from the robot_description topic
    spawn_entity = Node(package='ros_gz_sim', executable='create',
                        arguments=['-topic', 'robot_description',
                                   '-name', 'my_bot',
                                   '-z', '0.06'],
                        output='screen')

    # Bridge topics between ROS 2 and Gazebo Transport
    bridge_params = os.path.join(get_package_share_directory(package_name),'config','gz_bridge.yaml')
    ros_gz_bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        arguments=[
            '--ros-args',
            '-p',
            f'config_file:={bridge_params}',
        ]
    )


    # Launch them all!
    return LaunchDescription([
        rsp,
        # world_arg,
        # joystick,
        twist_mux,
        twist_stamper,
        gazebo,
        spawn_entity,
        ros_gz_bridge,
    ])
