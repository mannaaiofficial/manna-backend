import React, { useState, useRef, useEffect } from 'react';
import {
  View, Text, StyleSheet, SafeAreaView, TouchableOpacity, ActivityIndicator,
  Platform, TextInput, ScrollView, StatusBar, Modal, Alert, LayoutAnimation,
  UIManager, ImageBackground, KeyboardAvoidingView, Image
} from 'react-native';
import { CameraView, useCameraPermissions } from 'expo-camera';

// --- ANIMATION CONFIG ---
if (Platform.OS === 'android' && UIManager.setLayoutAnimationEnabledExperimental) {
  UIManager.setLayoutAnimationEnabledExperimental(true);
}

// --- 🎨 THEME --
const BG_DARK = '#0D0D0D';       
const CARD_DARK = '#1C1C1E';     
const ACCENT = '#D4F000';        
const TEXT_WHITE = '#FFFFFF';
const TEXT_SEC = '#8E8E93';
const INPUT_BG = '#2C2C2E';      

// --- 🔧 CONFIGURATION ---
// REPLACE THIS WITH YOUR CURRENT TUNNEL URL
const TUNNEL_URL = 'https://manna-backend-1.onrender.com'

// --- TYPES ---
type InventoryItem = { id: string; name: string; quantity: number; unit: string; daysLeft: number; icon: string };
type Ingredient = { name: string; amount: string };
type Recipe = { 
  id: string; type: string; title: string; description: string; 
  calories: number; macros: { p: number; c: number; f: number }; 
  time: string; difficulty: string; tip: string; 
  ingredients: Ingredient[]; instructions: string[]; image: string; 
};
type GroceryItem = { 
  name: string; amount: string; nutrition: string; 
  substitute: string; why: string; isExpanded?: boolean; // Added for UI toggle
};
type ChatMessage = { id: string; text: string; sender: 'user' | 'ai' };

// --- HELPERS ---
const getFoodIcon = (name: string): string => {
  const n = name.toLowerCase();
  if (n.includes('chicken')) return '🍗';
  if (n.includes('beef')) return '🥩';
  if (n.includes('egg')) return '🥚';
  if (n.includes('milk') || n.includes('yogurt')) return '🥛';
  if (n.includes('avocado')) return '🥑';
  if (n.includes('spinach') || n.includes('kale')) return '🥬';
  if (n.includes('rice') || n.includes('bread')) return '🍚';
  if (n.includes('apple') || n.includes('banana')) return '🍎';
  return '🥗';
};

// --- COMPONENTS ---

// 1. CAMERA COMPONENT
function FoodScanner({ visible, onClose, onScan }: { visible: boolean; onClose: () => void, onScan: (items: InventoryItem[]) => void }) {
  const [permission, requestPermission] = useCameraPermissions();
  const [analyzing, setAnalyzing] = useState(false);
  
  useEffect(() => { if (visible) requestPermission(); }, [visible]);

  const handleTakePhoto = async () => {
    setAnalyzing(true);
    // SIMULATION: In the real app, we send the image to backend.
    // For MVP stability, we simulate a successful scan of common items.
    setTimeout(() => {
      setAnalyzing(false);
      const scannedItems: InventoryItem[] = [
        { id: Date.now().toString(), name: 'Avocados', quantity: 2, unit: 'pcs', daysLeft: 4, icon: '🥑' },
        { id: (Date.now()+1).toString(), name: 'Sourdough', quantity: 1, unit: 'loaf', daysLeft: 5, icon: '🍞' },
        { id: (Date.now()+2).toString(), name: 'Eggs', quantity: 6, unit: 'pcs', daysLeft: 10, icon: '🥚' }
      ];
      onScan(scannedItems);
      onClose();
      Alert.alert("Scan Complete", "Identified: Avocados, Bread, Eggs.");
    }, 2000);
  };

  if (!visible) return null;
  return (
    <Modal visible={visible} animationType="fade">
      <View style={{ flex: 1, backgroundColor: '#000' }}>
        {permission?.granted ? (
          <CameraView style={{ flex: 1 }} facing="back">
            <View style={styles.scannerOverlay}>
               <View style={styles.scannerBox} />
               <Text style={styles.scanText}>{analyzing ? "ANALYZING..." : "SCAN FRIDGE CONTENTS"}</Text>
            </View>
            <TouchableOpacity onPress={handleTakePhoto} style={styles.snapBtn}>
              {analyzing ? <ActivityIndicator color="#000" size="large" /> : <View style={styles.shutterBtn} />}
            </TouchableOpacity>
            <TouchableOpacity onPress={onClose} style={styles.closeScanBtn}><Text style={{color:'#fff', fontSize:20}}>✕</Text></TouchableOpacity>
          </CameraView>
        ) : (
          <View style={styles.centerContent}><Text style={{color:'#fff'}}>Camera permission needed</Text></View>
        )}
      </View>
    </Modal>
  );
}

const ProgressBar = ({ current, max, color, label }: any) => {
  const width = Math.min((current / max) * 100, 100);
  return (
    <View style={{ marginBottom: 15 }}>
      <View style={{flexDirection:'row', justifyContent:'space-between', marginBottom:5}}>
        <Text style={{fontSize:11, fontWeight:'800', color: TEXT_SEC, letterSpacing: 1}}>{label.toUpperCase()}</Text>
        <Text style={{fontSize:12, color: TEXT_WHITE, fontWeight:'bold'}}>{current} / {max}</Text>
      </View>
      <View style={{ height: 6, backgroundColor: '#333', borderRadius: 3, overflow:'hidden' }}>
        <View style={{ height: 6, backgroundColor: color, borderRadius: 3, width: `${width}%` }} />
      </View>
    </View>
  );
};

// --- MAIN APP ---
export default function App() {
  const [step, setStep] = useState(0); 
  const [activeTab, setActiveTab] = useState<'inventory' | 'grocery'>('inventory');
  const [showScanner, setShowScanner] = useState(false);
  const [loading, setLoading] = useState(false);
  
  // DATA STATES
  const [info, setInfo] = useState({ name: '' });
  const [inventory, setInventory] = useState<InventoryItem[]>([]);
  const [groceryList, setGroceryList] = useState<GroceryItem[]>([]); 
  const [aiRecipes, setAiRecipes] = useState<Recipe[]>([]);
  const [dailyStats, setDailyStats] = useState({ calories: 1200, protein: 85, goalCalories: 2200, goalProtein: 140 });
  const [answers, setAnswers] = useState<any>({});
  
  // PREFERENCES
  const [mealCount, setMealCount] = useState(3);
  const [shoppingDays, setShoppingDays] = useState(3);
  const [cookingVibe, setCookingVibe] = useState<'Speed' | 'Therapy' | 'Pro'>('Speed');

  // UI STATES
  const [selectedRecipe, setSelectedRecipe] = useState<Recipe | null>(null);
  const [newItemName, setNewItemName] = useState('');
  const [isKitchenMode, setIsKitchenMode] = useState(false);
  const [chatInput, setChatInput] = useState('');
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  
  const animate = () => { LayoutAnimation.configureNext(LayoutAnimation.Presets.easeInEaseOut); };
  const handleStepChange = (newStep: number) => { animate(); setStep(newStep); };

  // --- LOGIC: CHOICE HANDLER ---
  const handleStockedFridgeChoice = () => {
    // This is the new intermediate step
    handleStepChange(8.5); 
  };

  const handleManualLog = () => {
    // User wants to type items manually
    setInventory([]); // Start empty
    setActiveTab('inventory');
    handleStepChange(9); // Go to dashboard
    Alert.alert("Manual Mode", "Use the '+' button to add your ingredients.");
  };

  const handleScanAction = () => {
    // Open the scanner
    setShowScanner(true);
    // Note: The scanner component handles the navigation after scanning
  };

  // --- API CALLS ---
  const generateRecipesFromInventory = async () => {
    if (inventory.length === 0) { Alert.alert("Empty Kitchen", "Add items first!"); return; }
    setLoading(true);
    
    try {
      const response = await fetch(`${TUNNEL_URL}/api/recipes`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Bypass-Tunnel-Reminder': 'true' },
        body: JSON.stringify({ ingredients: inventory.map(i => i.name), vibe: cookingVibe })
      });
      const data = await response.json();
      setLoading(false);

      if (Array.isArray(data)) {
          setAiRecipes(data); 
      } else {
          throw new Error("Invalid AI Response");
      }
    } catch (e) {
      setLoading(false);
      Alert.alert("Connection Error", "Is the backend running?");
    }
  };

  const generateShoppingList = async () => {
    setLoading(true);
    try {
        const response = await fetch(`${TUNNEL_URL}/api/shop`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Bypass-Tunnel-Reminder': 'true' },
            body: JSON.stringify({ 
                days: shoppingDays,
                goal: answers[2] || 'Health',
                diet: answers[3] || 'Everything',
                vibe: cookingVibe
            })
        });

        const data = await response.json();
        setLoading(false);
        
        if (Array.isArray(data)) {
            setGroceryList(data);
            setActiveTab('grocery'); 
            handleStepChange(9); 
        } else {
             throw new Error("Invalid AI Response");
        }
    } catch (e) {
        setLoading(false);
        Alert.alert("Connection Error", "Check your tunnel URL.");
    }
  };

  const toggleGroceryItem = (index: number) => {
    animate();
    const newList = [...groceryList];
    newList[index].isExpanded = !newList[index].isExpanded;
    setGroceryList(newList);
  };

  return (
    <SafeAreaView style={styles.safe}>
      <StatusBar barStyle="light-content" />
      
      {/* --- DASHBOARD (STEP 9) --- */}
      {step === 9 && (
        <View style={{ flex: 1 }}>
          <View style={styles.dashHeader}>
            <View>
              <Text style={styles.welcomeText}>Hello, {info.name || 'Chef'}</Text>
              <Text style={styles.dateText}>Mode: {cookingVibe} • Goal: {answers[2] || 'Health'}</Text>
            </View>
            <TouchableOpacity onPress={() => handleStepChange(8)} style={styles.settingsBtn}><Text style={{fontSize:20}}>⚙️</Text></TouchableOpacity>
          </View>
          
          <View style={styles.trackerCard}>
            <View style={{flexDirection:'row', justifyContent:'space-between', alignItems:'flex-end', marginBottom:15}}>
                <Text style={styles.trackerTitle}>DAILY FUEL</Text>
                <Text style={{color: ACCENT, fontWeight:'bold'}}>{dailyStats.calories} / {dailyStats.goalCalories} kcal</Text>
            </View>
            <ProgressBar current={dailyStats.calories} max={dailyStats.goalCalories} color={ACCENT} label="Energy" />
          </View>

          <View style={styles.tabContainer}>
            <TouchableOpacity onPress={() => {animate(); setActiveTab('inventory')}} style={[styles.tab, activeTab === 'inventory' && styles.activeTab]}>
              <Text style={[styles.tabText, activeTab === 'inventory' && styles.activeTabText]}>Inventory</Text>
            </TouchableOpacity>
            <TouchableOpacity onPress={() => {animate(); setActiveTab('grocery')}} style={[styles.tab, activeTab === 'grocery' && styles.activeTab]}>
              <Text style={[styles.tabText, activeTab === 'grocery' && styles.activeTabText]}>Shopping List</Text>
            </TouchableOpacity>
          </View>

          <ScrollView contentContainerStyle={{ paddingHorizontal: 20, paddingBottom: 100 }}>
            {/* INVENTORY TAB */}
            {activeTab === 'inventory' && (
              <>
                <View style={styles.addBar}>
                  <TextInput style={styles.addInput} placeholder="Add item (e.g. Milk)..." placeholderTextColor="#666" value={newItemName} onChangeText={setNewItemName} />
                  <TouchableOpacity onPress={() => {
                      if(!newItemName) return;
                      setInventory([...inventory, { id: Date.now().toString(), name: newItemName, quantity: 1, unit: 'pc', daysLeft: 7, icon: getFoodIcon(newItemName) }]);
                      setNewItemName('');
                  }} style={styles.addBtn}><Text style={{color:'#000', fontSize:20}}>+</Text></TouchableOpacity>
                </View>

                {inventory.length === 0 && (
                   <View style={styles.emptyState}>
                       <Text style={{color:'#666', marginBottom:10}}>Your kitchen is empty.</Text>
                       <TouchableOpacity onPress={() => setShowScanner(true)} style={styles.smallBtn}><Text style={styles.btnTextSmall}>📸 Scan Fridge</Text></TouchableOpacity>
                   </View>
                )}

                <View style={{flexDirection:'row', flexWrap:'wrap', justifyContent:'space-between'}}>
                    {inventory.map(item => (
                    <View key={item.id} style={styles.itemChip}>
                        <Text style={{fontSize:24}}>{item.icon}</Text>
                        <View style={{marginLeft:10}}>
                            <Text style={styles.chipText}>{item.name}</Text>
                            <Text style={styles.chipSub}>{item.quantity} {item.unit} • {item.daysLeft}d left</Text>
                        </View>
                    </View>
                    ))}
                </View>

                <Text style={styles.sectionTitle}>AI CHEF RECOMMENDATIONS</Text>
                <TouchableOpacity onPress={generateRecipesFromInventory} style={styles.genBtn}>
                    {loading ? <ActivityIndicator color="#000" /> : <Text style={styles.genBtnText}>✨ GENERATE RECIPES</Text>}
                </TouchableOpacity>
                
                {aiRecipes.map(recipe => (
                  <TouchableOpacity key={recipe.id} style={styles.recipeCard} onPress={() => setSelectedRecipe(recipe)}>
                    <ImageBackground source={{uri: recipe.image}} style={styles.recipeImg}>
                        <View style={styles.recipeOverlay}>
                            <View style={{flexDirection:'row', marginBottom:10}}>
                                <View style={styles.pill}><Text style={styles.pillText}>{recipe.time}</Text></View>
                            </View>
                            <Text style={styles.recipeTitle}>{recipe.title}</Text>
                            <Text style={styles.recipeMeta}>{recipe.calories} kcal • {recipe.difficulty}</Text>
                        </View>
                    </ImageBackground>
                  </TouchableOpacity>
                ))}
              </>
            )}

            {/* GROCERY TAB (EXPANDABLE CARDS) */}
            {activeTab === 'grocery' && (
               <View style={styles.groceryContainer}>
                 <Text style={styles.groceryHeader}>SMART LIST ({groceryList.length})</Text>
                 {groceryList.length === 0 && <Text style={{color:'#666'}}>No plan generated yet.</Text>}

                 {groceryList.map((item, i) => (
                   <TouchableOpacity key={i} style={styles.groceryCard} onPress={() => toggleGroceryItem(i)} activeOpacity={0.8}>
                       <View style={styles.groceryTopRow}>
                           <View style={{flexDirection:'row', alignItems:'center'}}>
                                <View style={styles.checkCircle} />
                                <Text style={styles.groceryName}>{item.name}</Text>
                           </View>
                           <Text style={styles.groceryAmt}>{item.amount}</Text>
                       </View>
                       
                       {/* EXPANDABLE SECTION */}
                       {item.isExpanded && (
                           <View style={styles.expandedContent}>
                               <View style={styles.divider} />
                               <Text style={styles.whyText}>💡 <Text style={{fontWeight:'bold'}}>Why:</Text> {item.why}</Text>
                               
                               <View style={styles.detailRow}>
                                   <View style={styles.tag}><Text style={styles.tagText}>⚡️ {item.nutrition}</Text></View>
                                   <View style={styles.tag}><Text style={styles.tagText}>🔄 Swap: {item.substitute}</Text></View>
                               </View>
                           </View>
                       )}
                       {!item.isExpanded && <Text style={{color:'#444', fontSize:10, alignSelf:'center', marginTop:5}}>Tap for details</Text>}
                   </TouchableOpacity>
                 ))}
               </View>
            )}
          </ScrollView>
        </View>
      )}

      {/* --- WIZARD STEPS --- */}
      {step < 9 && step !== 8.5 && (
        <ScrollView contentContainerStyle={styles.wizardContainer}>
          {step === 0 && (
            <View style={styles.centerContent}>
              <Text style={styles.logo}>manna<Text style={{color: ACCENT}}>.ai</Text></Text>
              <Text style={styles.tagline}>Smart Kitchen. Zero Waste.</Text>
              <TouchableOpacity style={styles.mainBtn} onPress={() => handleStepChange(1)}><Text style={styles.btnText}>START</Text></TouchableOpacity>
            </View>
          )}
          
          {/* ... (Skipping Steps 1-7 for brevity, they are standard inputs) ... */}
          {/* Re-adding basic name input for context if needed */}
          {step === 1 && (
              <View style={styles.stepContent}>
                 <Text style={styles.qText}>What's your name?</Text>
                 <TextInput style={styles.input} value={info.name} onChangeText={t=>setInfo({...info, name:t})} placeholder="Name" placeholderTextColor="#666"/>
                 <TouchableOpacity style={styles.mainBtn} onPress={()=>handleStepChange(2)}><Text style={styles.btnText}>NEXT</Text></TouchableOpacity>
              </View>
          )}
           {step === 2 && (
              <View style={styles.stepContent}>
                 <Text style={styles.qText}>What is your Goal?</Text>
                 {['Weight Loss', 'Energy', 'Muscle', 'Gut Health'].map(g => (
                     <TouchableOpacity key={g} style={styles.optionBtn} onPress={()=>{setAnswers({...answers, 2:g}); handleStepChange(3)}}><Text style={styles.optionText}>{g}</Text></TouchableOpacity>
                 ))}
              </View>
          )}
           {step === 3 && (
              <View style={styles.stepContent}>
                 <Text style={styles.qText}>Dietary Type?</Text>
                 {['Classic', 'Vegan', 'Vegetarian', 'Gluten Free'].map(g => (
                     <TouchableOpacity key={g} style={styles.optionBtn} onPress={()=>{setAnswers({...answers, 3:g}); handleStepChange(4)}}><Text style={styles.optionText}>{g}</Text></TouchableOpacity>
                 ))}
              </View>
          )}
           {step === 4 && (
              <View style={styles.stepContent}>
                 <Text style={styles.qText}>Cooking Vibe?</Text>
                 {['Speed', 'Therapy', 'Pro'].map(g => (
                     <TouchableOpacity key={g} style={styles.optionBtn} onPress={()=>{setCookingVibe(g as any); handleStepChange(8)}}><Text style={styles.optionText}>{g}</Text></TouchableOpacity>
                 ))}
              </View>
          )}

          {step === 8 && (
            <View style={styles.stepContent}>
              <Text style={styles.qText}>Kitchen Status?</Text>
              <TouchableOpacity style={styles.optionBtn} onPress={() => handleStepChange(8.5)}><Text style={styles.optionText}>🥦 Stocked Fridge</Text></TouchableOpacity>
              <TouchableOpacity style={styles.optionBtn} onPress={() => {setStep(8.9);}}><Text style={styles.optionText}>🏚 Empty Fridge</Text></TouchableOpacity>
            </View>
          )}

           {/* Empty Fridge Flow -> Shopping List Config */}
           {step === 8.9 && (
               <View style={styles.stepContent}>
                   <Text style={styles.qText}>Shopping for how many days?</Text>
                   <Text style={{color:ACCENT, fontSize:60, fontWeight:'bold', textAlign:'center', marginVertical:30}}>{shoppingDays}</Text>
                   <View style={{flexDirection:'row', justifyContent:'center', gap:20, marginBottom:30}}>
                        <TouchableOpacity onPress={()=>setShoppingDays(d=>Math.max(1,d-1))} style={styles.counterBtn}><Text style={{fontSize:24}}>-</Text></TouchableOpacity>
                        <TouchableOpacity onPress={()=>setShoppingDays(d=>d+1)} style={styles.counterBtn}><Text style={{fontSize:24}}>+</Text></TouchableOpacity>
                   </View>
                   <TouchableOpacity style={styles.mainBtn} onPress={generateShoppingList}>
                       {loading ? <ActivityIndicator color="#000"/> : <Text style={styles.btnText}>GENERATE PLAN</Text>}
                   </TouchableOpacity>
               </View>
           )}
        </ScrollView>
      )}

      {/* --- NEW STEP: 8.5 (CHOICE) --- */}
      {step === 8.5 && (
          <View style={[styles.stepContent, {padding:30}]}>
              <TouchableOpacity onPress={()=>setStep(8)}><Text style={styles.backLink}>← Back</Text></TouchableOpacity>
              <Text style={styles.qText}>How to add items?</Text>
              <Text style={styles.tagline}>Scan your ingredients with AI or log them manually.</Text>
              
              <TouchableOpacity style={[styles.bigChoiceBtn, {borderColor: ACCENT}]} onPress={handleScanAction}>
                  <Text style={{fontSize:40, marginBottom:10}}>📸</Text>
                  <Text style={styles.bigChoiceTitle}>Smart Scan</Text>
                  <Text style={styles.bigChoiceSub}>Use camera to detect food</Text>
              </TouchableOpacity>

              <TouchableOpacity style={styles.bigChoiceBtn} onPress={handleManualLog}>
                  <Text style={{fontSize:40, marginBottom:10}}>📝</Text>
                  <Text style={styles.bigChoiceTitle}>Manual Log</Text>
                  <Text style={styles.bigChoiceSub}>Type items list</Text>
              </TouchableOpacity>
          </View>
      )}

      {/* --- SCANNERS & MODALS --- */}
      <FoodScanner visible={showScanner} onClose={() => setShowScanner(false)} onScan={(items) => {
          setInventory([...inventory, ...items]);
          setActiveTab('inventory');
          handleStepChange(9);
      }} />

      {/* RECIPE MODAL (Simplified for brevity, similar to before) */}
      <Modal visible={!!selectedRecipe} animationType="slide" presentationStyle="pageSheet">
        {selectedRecipe && (
          <View style={{flex:1, backgroundColor:BG_DARK}}>
             <ImageBackground source={{uri: selectedRecipe.image}} style={{height:300, padding:20, justifyContent:'flex-end'}}>
                 <TouchableOpacity onPress={()=>setSelectedRecipe(null)} style={styles.closeModalBtn}><Text style={{color:'#fff', fontSize:20}}>✕</Text></TouchableOpacity>
                 <Text style={styles.modalTitle}>{selectedRecipe.title}</Text>
             </ImageBackground>
             <ScrollView style={{padding:20}}>
                 <Text style={{color:TEXT_SEC, fontSize:16, marginBottom:20}}>{selectedRecipe.description}</Text>
                 
                 <Text style={styles.sectionTitle}>INGREDIENTS</Text>
                 {selectedRecipe.ingredients.map((ing, i) => (
                     <View key={i} style={{flexDirection:'row', justifyContent:'space-between', paddingVertical:10, borderBottomWidth:1, borderColor:'#333'}}>
                         <Text style={{color:TEXT_WHITE}}>{ing.name}</Text>
                         <Text style={{color:ACCENT}}>{ing.amount}</Text>
                     </View>
                 ))}

                 <Text style={styles.sectionTitle}>INSTRUCTIONS</Text>
                 {selectedRecipe.instructions.map((inst, i) => (
                     <Text key={i} style={{color:'#ccc', marginBottom:15, lineHeight:22}}>{i+1}. {inst}</Text>
                 ))}
                 
                 <TouchableOpacity style={styles.mainBtn} onPress={()=>setSelectedRecipe(null)}><Text style={styles.btnText}>I COOKED THIS</Text></TouchableOpacity>
                 <View style={{height:50}}/>
             </ScrollView>
          </View>
        )}
      </Modal>

    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: BG_DARK },
  dashHeader: { padding: 20, flexDirection:'row', justifyContent:'space-between', alignItems:'center' },
  welcomeText: { fontSize: 24, fontWeight: 'bold', color: TEXT_WHITE },
  dateText: { fontSize: 14, color: TEXT_SEC },
  settingsBtn: { padding: 10, backgroundColor: INPUT_BG, borderRadius: 20 },
  trackerCard: { marginHorizontal: 20, backgroundColor: CARD_DARK, padding: 20, borderRadius: 25, marginBottom: 25 },
  trackerTitle: { fontSize: 13, fontWeight: '900', color: TEXT_SEC, letterSpacing: 1 },
  tabContainer: { flexDirection: 'row', marginHorizontal: 20, backgroundColor: INPUT_BG, borderRadius: 30, padding: 5, marginBottom: 25 },
  tab: { flex: 1, paddingVertical: 12, alignItems: 'center', borderRadius: 25 },
  activeTab: { backgroundColor: ACCENT },
  tabText: { fontWeight: '600', color: TEXT_SEC },
  activeTabText: { color: '#000', fontWeight: '800' },
  addBar: { flexDirection: 'row', marginBottom: 20 },
  addInput: { flex: 1, backgroundColor: INPUT_BG, borderRadius: 25, padding: 16, marginRight: 10, color: TEXT_WHITE, fontSize: 16 },
  addBtn: { backgroundColor: ACCENT, width: 50, borderRadius: 25, alignItems:'center', justifyContent:'center' },
  emptyState: { alignItems:'center', padding:20 },
  itemChip: { flexDirection: 'row', alignItems:'center', backgroundColor: CARD_DARK, padding: 15, borderRadius: 20, marginBottom: 10, width: '48%' },
  chipText: { fontSize: 16, fontWeight: '600', color: TEXT_WHITE },
  chipSub: { fontSize: 12, color: TEXT_SEC },
  sectionTitle: { fontSize: 14, fontWeight: '900', color: TEXT_SEC, marginTop: 25, marginBottom: 15, letterSpacing: 1 },
  recipeCard: { height: 240, borderRadius: 30, overflow: 'hidden', marginBottom: 20 },
  recipeImg: { width: '100%', height: '100%', justifyContent:'flex-end' },
  recipeOverlay: { backgroundColor: 'rgba(0,0,0,0.7)', padding: 20 },
  recipeTitle: { fontSize: 22, fontWeight: 'bold', color: TEXT_WHITE },
  recipeMeta: { color: ACCENT, fontWeight: 'bold', marginTop: 5 },
  pill: { backgroundColor: 'rgba(255,255,255,0.2)', paddingHorizontal:12, paddingVertical:6, borderRadius:10, marginRight:8 },
  pillText: { color: '#fff', fontWeight:'bold', fontSize:12 },
  groceryContainer: { backgroundColor: CARD_DARK, padding:20, borderRadius: 25, minHeight:300 },
  groceryHeader: { fontSize:14, fontWeight:'900', color: TEXT_WHITE, marginBottom:15, letterSpacing: 1 },
  groceryCard: { backgroundColor: '#252525', borderRadius: 20, padding: 15, marginBottom: 15 },
  groceryTopRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  checkCircle: { width: 22, height: 22, borderRadius: 11, borderWidth: 2, borderColor: '#555', marginRight: 15 },
  groceryName: { fontSize: 18, fontWeight: '700', color: TEXT_WHITE },
  groceryAmt: { fontSize: 16, color: ACCENT, fontWeight: 'bold' },
  expandedContent: { marginTop: 15 },
  divider: { height: 1, backgroundColor: '#444', marginBottom: 10 },
  whyText: { color: '#ddd', fontSize: 14, fontStyle: 'italic', marginBottom: 10 },
  detailRow: { flexDirection: 'row', gap: 10 },
  tag: { backgroundColor: '#333', padding: 8, borderRadius: 8 },
  tagText: { color: ACCENT, fontSize: 12, fontWeight: 'bold' },
  wizardContainer: { flexGrow: 1, padding: 30 },
  centerContent: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  stepContent: { flex: 1, paddingTop: 40 },
  logo: { fontSize: 42, fontWeight: '900', color: TEXT_WHITE, marginBottom: 10 },
  tagline: { fontSize: 16, color: TEXT_SEC, marginBottom: 50 },
  mainBtn: { backgroundColor: ACCENT, paddingVertical: 20, borderRadius: 30, width: '100%', alignItems: 'center', marginTop: 30 },
  btnText: { color: '#000', fontSize: 16, fontWeight: '900', letterSpacing: 1 },
  qText: { fontSize: 32, fontWeight: '800', color: TEXT_WHITE, marginBottom: 30 },
  input: { backgroundColor: INPUT_BG, padding: 20, borderRadius: 20, fontSize: 18, color: TEXT_WHITE },
  optionBtn: { backgroundColor: CARD_DARK, padding: 22, borderRadius: 20, marginBottom: 12, borderWidth: 1, borderColor: '#333' },
  optionText: { fontSize: 18, fontWeight: '600', color: TEXT_WHITE },
  backLink: { color: ACCENT, fontWeight: 'bold', marginBottom: 20, fontSize: 16 },
  bigChoiceBtn: { backgroundColor: CARD_DARK, padding: 30, borderRadius: 25, alignItems: 'center', marginBottom: 20, borderWidth: 1, borderColor: '#333' },
  bigChoiceTitle: { fontSize: 22, fontWeight: 'bold', color: TEXT_WHITE, marginBottom: 5 },
  bigChoiceSub: { color: TEXT_SEC },
  counterBtn: { width:60, height:60, borderRadius:30, backgroundColor: ACCENT, alignItems:'center', justifyContent:'center'},
  scannerOverlay: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  scannerBox: { width: 250, height: 250, borderWidth: 2, borderColor: ACCENT, borderRadius: 30 },
  scanText: { color: ACCENT, marginTop: 20, fontWeight: 'bold', letterSpacing: 2 },
  snapBtn: { position: 'absolute', bottom: 50, alignSelf: 'center', width: 80, height: 80, borderRadius: 40, borderWidth: 4, borderColor: '#fff', alignItems: 'center', justifyContent: 'center' },
  shutterBtn: { width: 60, height: 60, borderRadius: 30, backgroundColor: ACCENT },
  closeScanBtn: { position: 'absolute', top: 50, right: 20, backgroundColor: 'rgba(0,0,0,0.5)', width: 40, height: 40, borderRadius: 20, alignItems: 'center', justifyContent: 'center' },
  genBtn: { backgroundColor: ACCENT, padding: 15, borderRadius: 20, alignItems: 'center', marginBottom: 20, alignSelf: 'center', width: '100%' },
  genBtnText: { fontWeight: '900', color: '#000' },
  closeModalBtn: { position: 'absolute', top: 40, right: 20, backgroundColor: 'rgba(0,0,0,0.5)', width: 40, height: 40, borderRadius: 20, alignItems: 'center', justifyContent: 'center' },
  modalTitle: { fontSize: 28, fontWeight: '900', color: '#fff' },
  smallBtn: { backgroundColor: INPUT_BG, paddingHorizontal: 15, paddingVertical: 10, borderRadius: 15 },
  btnTextSmall: { color: TEXT_WHITE, fontWeight: 'bold' }
}); 