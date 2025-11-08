import google as genai 
import logging
import time
import json 


logger = logging.getLogger(__name__)

class GeminiAIIntegration:
    """
    Handles integration with the Google Gemini AI API for system analysis, 
    optimization suggestions, and conceptual hardware/software flux enhancement.
    """
    def __init__(self):
        self.api_key = None
        self.model = None
        self.ai_enabled = False
        logger.info("GeminiAIIntegration initialized.")

    def set_api_key(self, api_key):
        """Sets the Gemini API key and configures the generative model."""
        if api_key and api_key != "YOUR_GEMINI_API_KEY":
            self.api_key = api_key
            try:
                google.genai(api_key=self.api_key)
                # Use a reliable and capable model for complex analysis
                self.model = genai.GenerativeModel('gemini-1.5-flash') 
                self.ai_enabled = True
                logger.info("Gemini API Key set and model configured.")
            except Exception as e:
                logger.error(f"Failed to configure Gemini AI: {e}")
                self.model = None
                self.ai_enabled = False
                # Re-raise to alert the user in the GUI
                raise ValueError(f"Invalid Gemini API Key or configuration issue: {e}")
        else:
            self.api_key = None
            self.model = None
            self.ai_enabled = False
            logger.warning("Gemini API Key is empty or placeholder. Will use simulated responses.")
            
    def _generate_simulated_response(self, system_data):
        """Generates a highly detailed simulated AI response."""
        logger.info("Generating highly detailed simulated AI response.")
        
        # Dynamic simulation based on a few key metrics
        cpu_u = float(system_data.get('CPU Usage (%)', 0))
        mem_u = float(system_data.get('Memory Usage (%)', 0))
        temp_c = float(system_data.get('CPU Temp (°C)', 0))
        
        analysis = "System Status: Nominal. Baseline performance is within acceptable thresholds."
        root_cause = "No critical root causes. Minor resource fluctuations due to background OS tasks."
        suggestions = ["Monitor high-usage applications if load increases.", "Run a routine disk cleanup."]
        commands = []
        hardware_enhancements = ["Evaluate RAM frequency upgrade for increased throughput.", "Consider upgrading to an NVMe drive for I/O acceleration."]

        if cpu_u > 70 and temp_c > 80:
            analysis = "System Status: CRITICAL. Severe thermal throttling likely due to high CPU load."
            root_cause = "Sustained high CPU usage coupled with inadequate cooling solution."
            suggestions.insert(0, "IMMEDIATELY check cooling system and reduce active processes.")
            commands.insert(0, "taskkill /IM top_process.exe" if platform.system() == "Windows" else "killall -9 top_process")
            hardware_enhancements.insert(0, "HIGH PRIORITY: Upgrade to a high-performance AIO or custom loop cooler.")

        # Simulate conceptual enhancements for a high-level response
        conceptual_enhancements = [
            f"AI-Driven Optimization of Transistor Gating Logic: Proposing a sweep to clean up 'unwanted impurities' in hardware-software transit via simulated logic restructuring.",
            f"Software-Hardware Flux Stabilization: Recommending a kernel-level optimization (Simulated) to reduce latency in I/O Saturation by {round(random.uniform(5, 15), 1)}%.",
            "Enhancing Electrical Controlled Pulses: Suggesting a frequency smoothing algorithm (Simulated) to stabilize computational power delivery."
        ]
        
        response_content = {
            "analysis": analysis,
            "root_cause": root_cause,
            "optimization_suggestions": suggestions,
            "correction_commands": commands,
            "hardware_enhancements": hardware_enhancements,
            "conceptual_enhancements": conceptual_enhancements,
            "generated_by": "Simulated AI Algorithm v2.0 (High Detail)"
        }
        
        time.sleep(random.uniform(2, 5)) # Simulate API call latency
        return response_content

    def call_gemini_api(self, system_data):
        """
        Calls the Gemini API with the system data for high-level analysis and enhancement planning.
        Falls back to simulated response if the API key is not configured or fails.
        """
        if not self.ai_enabled:
            return self._generate_simulated_response(system_data)

        logger.info("Calling Gemini AI for comprehensive system analysis.")
        
        # Prepare the structured prompt with all 40+ attributes
        prompt = f"""
        You are an Advanced Hardware-Software Optimization AI (ASPE-AI).
        Analyze the following comprehensive system performance data snapshot. 
        Your goal is to identify bottlenecks, suggest actionable software optimizations, and provide highly detailed, conceptual hardware-software 'static exchange' enhancement recommendations to stabilize and improve performance.

        System Snapshot (40+ Attributes):
        {json.dumps(system_data, indent=2)}

        Provide your response in a structured JSON format with the following five keys. Ensure 'conceptual_enhancements' includes detailed, high-level, and complex suggestions related to 'transistor flux', 'circuitry integrity', and 'electrical controlled pulses' as if you are advising a component engineer:
        - "analysis": A concise summary of detected anomalies or system status (e.g., "Critical thermal issue identified").
        - "root_cause": The likely root cause(s) (e.g., "High CPU usage combined with a worn-out fan.").
        - "optimization_suggestions": A list of human-readable, actionable software optimization suggestions.
        - "correction_commands": A list of hypothetical, platform-agnostic administrative commands for immediate action (e.g., "Identify_PID_and_Kill", "Clean_Cache").
        - "hardware_enhancements": A list of specific physical hardware upgrade recommendations.
        - "conceptual_enhancements": A list of detailed, high-complexity, hypothetical/conceptual recommendations for 'internal static exchange' and 'transistor' level optimizations.
        """

        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    temperature=0.8,  # High temperature for creative/complex conceptual suggestions
                    max_output_tokens=1024, 
                )
            )
            
            response_text = response.text.strip()
            # Attempt to clean up and parse JSON (handle markdown wrappers)
            if response_text.startswith("```json"):
                response_text = response_text[7:].strip()
            if response_text.endswith("```"):
                response_text = response_text[:-3].strip()

            parsed_response = json.loads(response_text)
            logger.info("Gemini AI response parsed successfully.")
            return parsed_response

        except APIError as e:
            logger.error(f"Gemini API Error: {e}. Falling back to simulated response.", exc_info=True)
            return self._generate_simulated_response(system_data)
        except json.JSONDecodeError:
            logger.error("Failed to decode JSON response from Gemini. Falling back to simulated response.", exc_info=True)
            return self._generate_simulated_response(system_data)
        except Exception as e:
            logger.error(f"An unexpected error occurred during AI call: {e}. Falling back to simulated response.", exc_info=True)
            return self._generate_simulated_response(system_data)