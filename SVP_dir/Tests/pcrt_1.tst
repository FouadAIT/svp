<scriptConfig name="pcrt_1" script="PCRT">
  <params>
    <param name="phase_jump.test_num" type="int">1</param>
    <param name="der.manual.slave_id" type="int">1</param>
    <param name="pvsim.terrasas.channel" type="string">1,2</param>
    <param name="der.manual.ipaddr" type="string">1.2.3.4</param>
    <param name="hil.opal.rt_lab_model" type="string">3PhaseGeneric</param>
    <param name="phase_jump.n_iter" type="int">5</param>
    <param name="phase_jump_startup.eut_startup_time" type="int">10</param>
    <param name="pvsim.terrasas.ipaddr" type="string">127.0.0.1</param>
    <param name="pvsim.terrasas.vmp" type="float">460.0</param>
    <param name="pvsim.terrasas.overvoltage" type="float">660.0</param>
    <param name="der.manual.ipport" type="int">999</param>
    <param name="pvsim.terrasas.pmp" type="float">3000.0</param>
    <param name="das.mode" type="string">Disabled</param>
    <param name="pvsim.terrasas.curve_type" type="string">EN50530</param>
    <param name="hil.opal.hil_config" type="string">False</param>
    <param name="hil.opal.project_name" type="string">IEEE 1547.1 Phase Jump.llp</param>
    <param name="der.mode" type="string">Manual</param>
    <param name="hil.opal.hil_config_compile" type="string">No</param>
    <param name="hil.mode" type="string">Opal-RT</param>
    <param name="hil.opal.target_name" type="string">RTServer</param>
    <param name="pvsim.mode" type="string">TerraSAS</param>
    <param name="hil.opal.hil_config_open" type="string">Yes</param>
    <param name="hil.opal.hil_config_stop_sim" type="string">Yes</param>
    <param name="hil.opal.hil_config_load" type="string">Yes</param>
    <param name="hil.opal.hil_config_execute" type="string">Yes</param>
    <param name="hil.opal.project_dir" type="string">\OpalRT\IEEE_1547.1_Phase_Jump\</param>
    <param name="hil.opal.rt_lab_model_dir" type="string">\OpalRT\IEEE_1547.1_Phase_Jump\models</param>
  </params>
</scriptConfig>
