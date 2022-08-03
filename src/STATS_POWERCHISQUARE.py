import math, spss
import sys,os
from extension import Template, Syntax, processcmd
from pathlib import Path
import platform
import tempfile

path = os.path.splitext(__file__)[0]
sys.path.append(path)

from statjson import *

tempdir = Path("/tmp" if platform.system().lower() == "darwin" else tempfile.gettempdir())
tmp_folder = Path(tempdir)
testfile = tmp_folder / "test.json"

# Functions

def Run(args):
  global print_debug
  global color_name
  global color_label
  global size_name
  global size_label
  global printback

  import spss
  printback = spss.GetSetting("PRINTBACK")
  if printback.upper() in ["YES","LISTING"]:
    spss.Submit("PRESERVE.\nSET PRINTBACK OFF.")

  args = args[list(args.keys())[0]]
  
  y=str(args).find("PRINT_DEBUG")
  print_debug = (y > 0)

  oobj = Syntax([
    Template("OBSERVED", subc="PARAMETERS", ktype="literal", var="observed", islist="True"),
    Template("EXPECTED", subc="PARAMETERS", ktype="literal", var="expected", islist="True"),
    Template("COLUMNS", subc="PARAMETERS", ktype="literal", var="columns"),
    Template("ALPHA", subc="PARAMETERS", ktype="literal", var="alpha", islist="True"),
    Template("ES", subc="PARAMETERS", ktype="literal", var="effect_size", islist="True"),
    Template("DF", subc="PARAMETERS", ktype="literal", var="df", islist="True"),
    Template("N", subc="PARAMETERS", ktype="literal", var="n", islist="True"),
    Template("POWER", subc="PARAMETERS", ktype="literal", var="power", islist="True"),
    Template("DISPLAY", subc="PLOT", ktype="str", var="graph", vallist=["yes","no"])])

  if print_debug:
    print("ARGS")

  if "HELP" in args:
    helper()
  else:
    processcmd(oobj,args,do_work)

def helper():
    # Open html help in default browser window
    # The location is computed from the current module name
    
    import webbrowser, os.path
    path = os.path.splitext(__file__)[0]
    helpspec = "file://" + path + os.path.sep + "STATS_POWERCHISQUARE.html"
    
    # webbrowser.open seems not to work well
    browser = webbrowser.get()
    if not browser.open_new(helpspec): print(("Help file not found:" + helpspec))

def ReturnLists (X_Label, Y_Label, vLabels, Data, X_Axis, Y_Axis):
  Y_index=0
  X_index=0

  c=0
  for i in vLabels:
    c=c+1
    if i == X_Label:
      X_index=c
    elif i == Y_Label:
      Y_index=c

  c=0
  for i in Data:
    for j in i:
      c=c+1
      if c == X_index:
        X_Axis.append(j)
      elif c == Y_index:
        Y_Axis.append(j)
    c=0

def GetExpectedValues (o, rowsum, colsum, cols):
  global n
  matrix=[]
  e=[]
  c=1
  r=1
  count=0
  rsum=0
  csum=0
  n=0

  for i in o:
    matrix.append([c,i])
    count=count+1
    c=c+1
    n=n+i
    rsum=rsum+i
    if count % cols == 0:
      c=1
      r=r+1
      rowsum.append(rsum)
      rsum=0

  for x in range(1,cols+1):
    csum=0
    for c,v in matrix:
      if x == c:
        csum=csum+v
    colsum.append(csum)

  c=0
  for i in rowsum:
    for j in colsum:
      c=c+1
      e.append((i*j)/n)

  return e

######
def ConstructSyntax (p,d):
  s = ''
  if p == 0:
    syntax="DATA LIST FREE / ChiSq Effect_Size alpha df numcases." + \
           "\nBEGIN DATA." + d + "\nEND DATA.\nEXECUTE." + \
           "\nCOMPUTE #IDF_CHISQ=IDF.CHISQ(1-alpha,df)." + \
           "\nCOMPUTE POWER=1-NCDF.CHISQ(#IDF_CHISQ,df,ChiSq)." + \
           "\nFORMATS POWER chisq (F10.4) power effect_size (F10.7) df (F10) alpha (F10.3)." + \
           "\nVARIABLE LABELS ChiSq 'Chi-Square' power 'Estimated Power'" + \
           "\n Effect_Size 'Effect Size' alpha 'Sig.' df 'df' numcases 'N'."
  else:
    syntax="DATA LIST FREE / effect_size alpha df requested_power." + \
           "\nBEGIN DATA." + d + "\nEND DATA.\nEXECUTE." + \
           "\nCOMPUTE chi_critical_value=idf.chisq(1-alpha,df)." + \
           "\nCOMPUTE upper_limit=chi_critical_value*10." + \
           "\nCOMPUTE step=chi_critical_value * .0001." + \
           "\nLOOP #CHISQ=(chi_critical_value+step) TO upper_limit BY step." + \
           "\nCOMPUTE ACTUAL_POWER=1-NCDF.CHISQ(chi_critical_value,df,#CHISQ)." + \
           "\nDO IF ACTUAL_POWER GE requested_power." + \
           "\nCOMPUTE chi_at_power=#CHISQ." + \
           "\nBREAK." + \
           "\nEND IF." + \
           "\nEND LOOP." + \
           "\nCOMPUTE N=chi_at_power/(effect_size**2)." + \
           "\nCOMPUTE N_ROUND=RND(N)." + \
           "\nMATCH FILES /FILE=* /KEEP effect_size alpha df requested_power actual_power chi_at_power n_round.\nEXECUTE." + \
           "\nFORMATS chi_at_power (F10.4) actual_power effect_size (F10.7) df (F10) alpha (F10.3)." + \
           "\nVARIABLE LABELS chi_at_power 'Chi-Square at Desired Power' actual_power 'Actual Power'" + \
           "\n Effect_Size 'Effect Size' alpha 'Sig.' df 'df' n_round 'Number of Cases Needed'" + \
           "\n requested_power 'Requested Power'."
           
  s = "PRESERVE.\nSET DECIMAL=DOT.\n" + syntax + "\nRESTORE."         

  return s

def CreateCellInformationTable(rows,cols,OBS,EXP,proportion,proc):

  row_labels=[]
  col_labels=[]
  cellinfo_footnotes=[]
  OE=[]
  TABLE_DATA=()

  for y in range(1,rows+1):
    for z in range(1,3):
      if z == 1:
        row_labels.append(str(y) + " Observed")
      else:
        row_labels.append(str(y) + " Expected") 

  for i in range(1,cols+1):
    col_labels.append("Col_" + str(i))

  for x in range(0,len(OBS),cols):
    for y in range(1,3):
      for z in range(x,x+cols):
        if y == 1:
          OE.append(OBS[z])
        else:
          OE.append(EXP[z])      

  TABLE_DATA = tuple([OE[x:x+cols] for x in range(0, len(OE), cols)])

  f1="Observed and Expected"
  if proportion == True:
    f2="Values are proportions"
  else:
    f2="Values are cell counts"

  cellinfo_footnotes=[f1,f2]
  
  test_table=Table("Cell Information","CellInfo")
  test_table.update_title(footnote_refs=[0,1])
  test_table.set_default_cell_format(decimals=3)
  test_table.add_dimension(Table.DimensionType.ROWS,'Row',True,row_labels)
  test_table.add_dimension(Table.DimensionType.COLUMNS,'Columns',False,col_labels)

  for i in TABLE_DATA:
    test_table.add_cells(i)

  test_table.add_footnotes(cellinfo_footnotes)

  proc.add_table(test_table)

def CreateChart(varied,FindingN,MyData,varLabels,proc):

  X_Axis = []
  Y_Axis = []
  X_title = ''
  Y_title = ''
  X_label = ''
  Y_label = ''
    
  if varied == "alpha":
    X_label = "Sig."
    X_chart_title = "Alpha Level"
    X_title = "Alpha"
    
  elif varied == "degrees_of_freedom":
    X_label = "df"
    X_chart_title = "Degrees of Freedom"
    X_title = "Df"
      
  elif varied == 'effect_size':
    X_label = "Effect Size"
    X_chart_title = "Effect Size"
    X_title = "Effect Size"
    
  elif varied == 'sample_n':
    X_label = "N"
    X_chart_title = "Sample Size"
    X_title = "Sample Size"
  
  elif varied == 'power':
    X_label = "Requested Power"
    X_chart_title = "Power"
    X_title = "Power"
      
  if FindingN:
    Y_title = "Estimated Sample Size"
    Y_label = "Number of Cases Needed"
  else:
    Y_title = "Estimated Power"
    Y_label = "Estimated Power"
  
  #  print(varied)  print(X_label)  print(Y_label)  print(varLabels) # print(MyData)
  #  print(X_Axis)  print(Y_Axis)
  
  ReturnLists(X_label,Y_label,varLabels, MyData, X_Axis, Y_Axis)
    
  chart_title = Y_title + " by " + X_chart_title
  tree_title = Y_title + " by " + X_chart_title
    
  chisq_chart = Chart(chart_title,tree_title)
  chisq_chart.set_type(Chart.Type.Line)
  chisq_chart.set_axis_data(Chart.Axis.X, X_Axis)
  chisq_chart.set_axis_label(Chart.Axis.X, X_title)
  chisq_chart.set_axis_data(Chart.Axis.Y, Y_Axis)
  chisq_chart.set_axis_label(Chart.Axis.Y, Y_title)
  proc.add_chart(chisq_chart)

def CreatePowerTable(FindingN,iterations,TABLE_NAME,OMS_TITLE,varLabels,MyData,footnote2,proc):

  if FindingN:
    footnote1 = "1. Estimating sample size given power."
  else:
    footnote1 = "1. Estimating power given sample size."

  f=[]
  
  f.append(footnote1)
  f.append(footnote2)
  
  chisq_row=[]
  for i in range(1,iterations+1):
    chisq_row.append(str(i))
  
  chisq_table=Table(TABLE_NAME,OMS_TITLE)
  chisq_table.update_title(footnote_refs=[0,1])
  chisq_table.set_default_cell_format(decimals=3)
  chisq_table.add_dimension(Table.DimensionType.ROWS,'Model',True,chisq_row)
  chisq_table.add_dimension(Table.DimensionType.COLUMNS,'Statistics',False,varLabels)

  for i in MyData:
    chisq_table.add_cells(i)

  for i in f:
    i=i.replace('1. ','').replace('2. ','')
    chisq_table.add_footnotes(i)
  
  proc.add_table(chisq_table)

def GetPowerSyntax (o,e,proportion,test_n,cols,df,effect_size,a,n,power,equal_prob):
  chisq=0
  sample_size=n
  footnote=''

  #Rules:
  # Do not allow a table of counts and iterate over sample size at the same time
     
  #AS GIVEN IN COHEN(1988) ES = SQRT(NONCENTRALITY PARAMETER, aka LAMBDA / N)

  es=effect_size

  if es > 0:
    chisq=(es**2)*float(n)
    footnote = "2. Chi-Square=Effect-size**2 * N."
  else:
    if cols > 0:
      rows = len(o)/cols
      df = (rows-1) * (cols-1) 
    else:
      if len(o) > 0: df=len(o)-1

    if n == 0: n = test_n

    count=0
    cell=0
    for i in o:
      cell=((i-e[count])**2)/e[count]
      chisq=chisq+cell
      count=count+1

    #if the effect size comes from a proportion, es=sqrt(chisq)
    
    if proportion == True:
      es=math.sqrt(chisq)
      n=sample_size
      footnotes = "2. Chi-Square=Effect-size**2 * N."
      if sample_size > 0: chisq=chisq*n
    else:
      es=math.sqrt(chisq/n)
      if sample_size == 0:
        footnote = "2. N is rounded to the nearest whole number."
      else:
        footnote = "2. Chi-Square based on cell counts."

  if equal_prob == True: df = (cols-1)

  if power == 0:
    data_line="\n" + str(chisq) + "\t" + str(es) + "\t" + str(a) + "\t" + str(df) + "\t" + str(n)
  else:
    data_line="\n " + str(es) + "\t" + str(a) + "\t" + str(df) + "\t" + str(power)

  return footnote, data_line

def GetData():
  dataCursor=spss.Cursor()
  AllData=dataCursor.fetchall()
  dataCursor.close()  
  MyData = tuple(AllData)
  uniqueCount=len(set(AllData))

  return MyData, uniqueCount
  
def IterateOverValues(value_list,obs_cells,exp_cells,cols,df_list,es_list,\
                      alpha_list,n_list,power_list,varied,equal_prob):
    
  d=''
  proportion = False
  o=obs_cells
  e=exp_cells
  test_n=0
  footnote2=''
  syntax=''
  dataline = ''

  if o != []:
    for i in o:
      test_n=test_n+float(i)
    
    proportion=(int(round(test_n)) == 1)
    if proportion == False: test_n = int(round(test_n))
    
    if e == []:
      rowsum=[]
      colsum=[]
      if equal_prob == True:
        for i in o:
          e.append(test_n / len(o))
      else:
        e=GetExpectedValues(o,rowsum,colsum,cols)
      exp_cells = e

  if value_list == []:
    p=0
    es=0
    n=0
    df=0
    a=0
    if test_n > 0:
      #Finding power for just one case
      if len(alpha_list) > 0: a=float(alpha_list[0])
      if len(es_list) > 0: es=float(es_list[0])
      if len(power_list) > 0: p=float(power_list[0])
      if len(n_list) > 0: n=int(n_list[0])
      if len(df_list) > 0: df=int(df_list[0])

      if o != [] and proportion == False: n=test_n
      footnote2,dataline=GetPowerSyntax(o,e,proportion,test_n,cols,df,es,a,n,p,equal_prob)
      syntax = ConstructSyntax(p,dataline)

  else:
    for v in value_list:
      p=0
      es=0
      n=0
      df=0
      a=0
  
      if varied != 'alpha':
        if len(alpha_list) > 0: a=float(alpha_list[0])
      if varied != 'effect_size':
        if len(es_list) > 0: es=float(es_list[0])
      if varied != 'power':
        if len(power_list) > 0: p=float(power_list[0])
      if varied != 'sample_n':
        if len(n_list) > 0: n=int(n_list[0])
      if varied != 'degrees_of_freedom':
        if len(df_list) > 0: df=int(df_list[0])

      if varied == 'alpha':
        a=float(v)
      elif varied == 'effect_size':
        es=float(v)
      elif varied == 'power':
        p=float(v)
      elif varied == 'sample_n':
        n=int(v)
      elif varied == 'degrees_of_freedom':
        df=int(v)

      # If working with cell counts, we can't be finding N, only power for the test
      if o != [] and proportion == False: n=test_n      
      footnote2,dataline = GetPowerSyntax(o,e,proportion,test_n,cols,df,es,a,n,p,equal_prob)
      d=d+dataline
      syntax = ConstructSyntax(p,d)
      p=0
      es=0
      n=0
      a=0
      df=0
    # end loop over values

  return footnote2,exp_cells,syntax

def MakeJSONFile(proc,testfile):
  json2=proc.get_json()
  f=open(testfile,'w',encoding='utf-8')
  f.write(json2)
  f.close()
  t=str(testfile)
  return t

def MakeRangeValues(vals,var_type):
  elements=vals
  array=[]
  my_str=''
  to = False
  by = False
  for el in elements:
    els = str(el).upper().strip()
    if to == False: to = (els == "TO")
    if by == False: by = (els == "BY")

  if to == True:
    start=float(elements[0])
    stop=float(elements[2])
    if by == True:
      increment=float(elements[4])
    else:
      increment=1

    x=start
    while x <= stop:
      w=len(str(x))
      if '.' in str(x) and w > 8:
        w=5
        x=round(x,w)
      if var_type == "integer":
        fmt='{:'+ str(w) + '.0f' + '}'
        str_val=str(fmt.format(int(x)))
      else:
        fmt='{:'+ str(w) + '.' + str(w) +'}'
        str_val=str(fmt.format(x))

      if str_val[-1] == ".": str_val=str_val[0:len(str_val)-1]
      array.append(str_val)
      x=float(fmt.format(x+increment))
  else:
    array = vals

  return array

def WriteOutput (output):
  spss.Submit("OUTPUT CREATE /SPEC SOURCE=STATJSONFILE('" + output + "').")
  spss.Submit("ERASE FILE '" + output + "'.")

def WriteWarning (text,proc,testfile):
  warning_item = Warnings(text)
  proc.add_warnings(warning_item)
  t=MakeJSONFile(proc,testfile)
  WriteOutput(t)

def Convert(in_string):
  li = list(in_string.split(" "))
  return li
  
def Check_LT_Zero(inStr,inVals,valType):
  msg = ''
  EL = 0
  if len(inVals) > 0:
    for v in inVals:
      if valType == "int":
        val=int(v)
      else:
        val=float(v)
      if val <= 0:
        EL = 1
        print("Error check found problem with " + inStr)
        msg="At least one " + inStr.upper() + " value is <= 0."
        break
  return EL, msg
  
def ErrorCheck (es_list,power_list,n_list,alpha_list,df_list,obs_cells,exp_cells,cols):
  ErrorLev = 0
  m = ''
  
  if power_list == [] and n_list == [] and obs_cells == []:
    ErrorLev=1
    m="Either POWER or N must be specified."

  if es_list == [] and power_list == [] and n_list == [] and obs_cells == []:
    ErrorLev=1
    m="No valid parameter values found. Nothing to do."
  
  if ErrorLev == 0: ErrorLev, m = Check_LT_Zero("DF",df_list,"int")
  if ErrorLev == 0: ErrorLev, m = Check_LT_Zero("ALPHA",alpha_list,"float")
  if ErrorLev == 0: ErrorLev, m = Check_LT_Zero("N",n_list,"int")
  if ErrorLev == 0: ErrorLev, m = Check_LT_Zero("ES",es_list,"float")
  
  if ErrorLev == 0: 
    if len(obs_cells) > 0 and cols == 0:
      ErrorLev=1
      m="When OBSERVED values are used, COLUMNS must be > 0."

  if ErrorLev == 0: 
    if len(exp_cells) > 0 and len(obs_cells) == 0:
      ErrorLev=1
      m="EXPECTED values are specified, but OBSERVED values are not."

  if ErrorLev == 0:
    if len(power_list) > 0:
      for p in power_list:
        val=float(p)
        if val <= 0 or val >= 1:
          ErrorLev=1
          m="At least one POWER value is <= 0 or >= 1."
          break

  return ErrorLev, m
  
def do_work (observed=[],expected=[],columns=0,df=[],effect_size=[],\
             alpha=[.05],n=[],power=[],graph='YES'):

  ## DEFAULTS
  cols=0
  obs_cells=[]
  exp_cells=[]
  es_list=[]
  power_list=[]
  alpha_list=[]
  df_list=[]
  n_list=[]
  value_list=[]
  chisq_footnotes=[]
  cellinfo_footnotes=[]
  iterations=0  
  FindingN=0
  proportion = False
  equal_prob = False
  MyData=()
  DATA=[]
  uniqueCount=0
  varied=''
  OE=[]
  rows=0
  Error = False
  Procedure_Level_Error = False
  ErrorLevel = 0
  msg = ''
    
  PROC_NAME="Power Chi Square"
  PROC_LABEL="Power Analysis: Chi-Square"

  chisq_proc=StatJSON(PROC_NAME)
  
  cols=int(columns)

  if len(observed) > 1: obs_cells=[float(x) for x in observed]
  
  if len(expected) > 0:
    if str(expected).upper().find("EQUAL") > 0:
      equal_prob = True
      exp_cells=[]
    else:
      equal_prob = False
      exp_cells=[float(x) for x in expected]

  if df != []:
    temp = MakeRangeValues(df,"integer")
    df_list=[int(x) for x in temp]

  if effect_size != []:
    temp = MakeRangeValues(effect_size,"")
    es_list=[float(x) for x in temp] 

  if alpha != []:
    temp = MakeRangeValues(alpha,"")
    alpha_list=[float(x) for x in temp]

  if n != []:
    temp = MakeRangeValues(n,"integer")
    n_list=[int(x) for x in temp]
  
  if power != []:
    temp = MakeRangeValues(power,"")
    power_list=[float(x) for x in temp]
  else:
    power_list = []

  graph=graph.upper()
  
  l = len(obs_cells)
  
  if l > 0:
    if cols == 0: cols = int(l)
    rows = int(l/cols)
  
  if len(alpha_list) == 1: alpha_list[0] = alpha[0]
  if len(es_list) == 1: es_list[0] = effect_size[0]
  if len(df_list) == 1: df_list[0] = df[0]
  
  if len(alpha_list) > 1:
    value_list = alpha_list
    varied = 'alpha'
  elif len(es_list) > 1:
    value_list = es_list
    varied = 'effect_size'
  elif len(df_list) > 1:
    value_list = df_list
    varied = 'degrees_of_freedom'
  else:
    if len(power_list) >= 1:
      value_list = power_list
      varied = 'power'
    elif len(n_list) >= 1:
      value_list = n_list
      varied = 'sample_n'
    
  if n_list == [] and power_list == [] and obs_cells != []:
    varied = 'sample_n'
    FindingN = False
  else: 
    FindingN = (varied == 'power') or (varied != 'power' and n_list == [])

  iterations = len(value_list)
  
  ErrorLevel, msg = ErrorCheck(es_list,power_list,n_list,alpha_list,df_list,obs_cells,\
                               exp_cells,cols)
  if alpha_list == []:
    ErrorLevel = 2
    msg = "Alpha is not specified; using default of .05."
    alpha_list[0] = .05

  if ErrorLevel == 1:
    msg = msg + "\nThis command not executed."
    WriteWarning(msg,chisq_proc,testfile)
    Procedure_Level_Error = True
  elif ErrorLevel == 2:
    WriteWarning(msg,chisq_proc,testfile)
      
  if Procedure_Level_Error == False:
    footnote2,exp_cells,syntax = IterateOverValues(value_list,obs_cells,exp_cells,\
                                    cols,df_list,es_list,alpha_list,n_list,power_list,\
                                    varied,equal_prob)
    spss.Submit(syntax)
    MyData,uniqueCount = GetData()
    OBS=obs_cells
    EXP=exp_cells
    
    varlist=[]
    varLabels=[]
    varcount=spss.GetVariableCount()
    for i in range(varcount):
      varlist.append(spss.GetVariableName(i))
      varLabels.append(spss.GetVariableLabel(i))
      
    if OBS != []: CreateCellInformationTable (rows,cols,OBS,EXP,proportion,chisq_proc)

    if iterations == 0: iterations = 1
    CreatePowerTable(FindingN,uniqueCount,"Power Analysis Table","Power Analysis Table",\
                     varLabels,MyData,footnote2,chisq_proc)

    if graph == "YES": CreateChart(varied,FindingN,MyData,varLabels,chisq_proc)
          
    t=MakeJSONFile(chisq_proc,testfile)
    WriteOutput(t)

## end functions